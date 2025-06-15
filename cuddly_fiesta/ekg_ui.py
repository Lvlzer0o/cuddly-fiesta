"""Simple Tkinter-based GUI for real-time 12-lead ECG display."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Type, Optional

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .ecg_core import ArrhythmiaPattern, ECGCore
from .multi_lead import MultiLeadECG
from .ecg_baseline import ECGBaseline
from .waveform_segments import (
    AtrialFibrillation,
    NormalSinusRhythm,
    VentricularTachycardia,
)

# Ensure Tkinter backend for matplotlib
matplotlib.use("TkAgg")


class ECGGui:
    """Display a MultiLeadECG in a Tkinter window with basic controls."""

    def __init__(self, master: tk.Tk, show_grid: bool = False):
        self.master = master
        master.title("ECG Generator GUI")

        self.show_grid = show_grid
        self._grid_helper = None

        self.interval_ms = 40
        self.playback_speed = tk.DoubleVar(value=1.0)
        self.pattern_name = tk.StringVar(value="Normal Sinus Rhythm")
        self.highlight_lead = tk.StringVar(value="None")

        self.pattern_classes: Dict[str, Type[ArrhythmiaPattern]] = {
            "Normal Sinus Rhythm": NormalSinusRhythm,
            "Atrial Fibrillation": AtrialFibrillation,
            "Ventricular Tachycardia": VentricularTachycardia,
        }

        self._create_controls()
        self._create_figure()

        self.ecg_length_sec = 3
        self._setup_ecg()
        self.running = True
        self.frame_idx = 0
        self._update_plot()

    def _create_controls(self) -> None:
        ctrl_frame = ttk.Frame(self.master)
        ctrl_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(ctrl_frame, text="Pattern:").pack(side=tk.LEFT)
        pattern_menu = ttk.OptionMenu(
            ctrl_frame,
            self.pattern_name,
            self.pattern_name.get(),
            *self.pattern_classes.keys(),
            command=lambda _: self._setup_ecg(),
        )
        pattern_menu.pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl_frame, text="Speed:").pack(side=tk.LEFT)
        speed = ttk.Scale(
            ctrl_frame,
            from_=0.5,
            to=3.0,
            variable=self.playback_speed,
            orient=tk.HORIZONTAL,
            length=150,
        )
        speed.pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl_frame, text="Highlight:").pack(side=tk.LEFT)
        self.order = [
            "None",
            "I",
            "II",
            "III",
            "aVR",
            "aVL",
            "aVF",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
        ]
        highlight_menu = ttk.OptionMenu(
            ctrl_frame,
            self.highlight_lead,
            self.highlight_lead.get(),
            *self.order,
            command=lambda _: self._apply_highlight(),
        )
        highlight_menu.pack(side=tk.LEFT, padx=5)

        self.toggle_btn = ttk.Button(
            ctrl_frame, text="Pause", command=self._toggle_running
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

    def _create_figure(self) -> None:
        self.fig, self.axes = plt.subplots(
            4, 3, figsize=(12, 8), sharex=True, sharey=True
        )
        plt.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _setup_ecg(self) -> None:
        pattern_cls = self.pattern_classes[self.pattern_name.get()]
        pattern = pattern_cls()
        ecg = ECGCore(duration_sec=self.ecg_length_sec, sampling_rate=1000)
        pattern.apply_to_ecg(ecg)
        self.multi = MultiLeadECG(ecg)

        self.time = self.multi.time
        self.leads = [self.multi.leads[name] for name in self.order[1:]]

        for ax, name in zip(self.axes.ravel(), self.order[1:]):
            ax.cla()
            ax.set_xlim(0, ecg.duration_sec)
            ax.set_ylim(-2, 2)
            ax.set_title(name)
            ax.axhline(0, color="gray", linewidth=0.5)
            ax.set_xticks([])
            ax.set_yticks([])
            if self.show_grid:
                if self._grid_helper is None:
                    self._grid_helper = ECGBaseline(
                        ecg.duration_sec, ecg.sampling_rate
                    )
                self._grid_helper._add_ecg_grid(ax)

        self.lines = [
            ax.plot([], [], "k", linewidth=1)[0] for ax in self.axes.ravel()
        ]
        self.frame_idx = 0
        self._apply_highlight()
        self.canvas.draw()

    def _toggle_running(self) -> None:
        """Pause or resume the ECG animation."""
        self.running = not self.running
        self.toggle_btn.config(text="Resume" if not self.running else "Pause")
        if self.running:
            self._update_plot()

    def _apply_highlight(self) -> None:
        for ln, name in zip(self.lines, self.order[1:]):
            if name == self.highlight_lead.get():
                ln.set_color("red")
                ln.set_linewidth(2)
            else:
                ln.set_color("black")
                ln.set_linewidth(1)
        self.canvas.draw_idle()

    def _update_plot(self) -> None:
        """Periodically updates the ECG plot to create an animation.

        Advances the frame index based on playback speed, updates the data
        for each lead's line plot, and schedules the next call to itself
        via `self.master.after`.
        """
        if not self.running:
            return
        base_samples_per_update = (
            1000 * self.interval_ms
        ) / 1000.0  # Assumes 1000Hz sampling rate
        step = max(1, int(base_samples_per_update * self.playback_speed.get()))
        self.frame_idx = (self.frame_idx + step) % len(self.time)
        for ln, data in zip(self.lines, self.leads):
            ln.set_data(self.time[: self.frame_idx], data[: self.frame_idx])
        self.canvas.draw_idle()
        self.master.after(self.interval_ms, self._update_plot)


def main(argv: Optional[list[str]] = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="ECG GUI")
    parser.add_argument(
        "--grid", action="store_true", help="overlay ECG grid on plots"
    )
    args = parser.parse_args(argv)

    root = tk.Tk()
    ECGGui(root, show_grid=args.grid)
    root.mainloop()


if __name__ == "__main__":
    main()
