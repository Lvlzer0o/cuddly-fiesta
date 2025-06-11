# ECG GUI Interface using Tkinter
"""Graphical interface for visualizing 12-lead ECG data in real time.

This module provides a lightweight Tkinter GUI that displays all 12 leads
and updates them using a ``MultiLeadECG`` generator. Users can control
playback speed, switch arrhythmia patterns and highlight individual leads.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from typing import Callable, Dict, List

from ecg_core import ECGCore
from waveform_segments import NormalSinusRhythm


class MultiLeadECG:
    """Simple multi-lead ECG wrapper generating 12 synchronous leads."""

    def __init__(self, pattern: NormalSinusRhythm | None = None,
                 duration_sec: float = 10.0, sampling_rate: int = 500):
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)
        self.pattern = pattern or NormalSinusRhythm()

        # Create 12 ECGCore instances
        self.leads: List[ECGCore] = [
            ECGCore(duration_sec, sampling_rate) for _ in range(12)
        ]
        self.apply_pattern(self.pattern)

        self.index = 0

    def apply_pattern(self, pattern: NormalSinusRhythm) -> None:
        """Apply an arrhythmia pattern to all leads and reset playback."""
        self.pattern = pattern
        for core in self.leads:
            core.voltage[:] = 0
            core.segments_added = []
            pattern.apply_to_ecg(core)
        self.index = 0

    def step(self, num_samples: int) -> tuple[np.ndarray, List[np.ndarray], bool]:
        """Return the next chunk of samples for all leads and if data looped."""
        looped = False
        start = self.index
        end = min(start + num_samples, self.n_samples)
        self.index = end
        if end >= self.n_samples:
            self.index = 0
            looped = True

        time = self.leads[0].time[start:end]
        voltages = [lead.voltage[start:end] for lead in self.leads]
        return time, voltages, looped


class ECGGui(tk.Tk):
    """Tkinter-based viewer for multi-lead ECG traces."""

    def __init__(self) -> None:
        super().__init__()
        self.title("ECG Viewer")

        # Available patterns
        self.pattern_factories: Dict[str, Callable[[], NormalSinusRhythm]] = {
            "NSR 70 bpm": lambda: NormalSinusRhythm(heart_rate_bpm=70),
            "NSR 100 bpm": lambda: NormalSinusRhythm(heart_rate_bpm=100),
        }

        self.speed = tk.DoubleVar(value=1.0)
        self.pattern = tk.StringVar(value="NSR 70 bpm")
        self.highlight = tk.IntVar(value=1)

        self._create_widgets()

        self.ecg = MultiLeadECG(self.pattern_factories[self.pattern.get()]())
        self._init_plot()
        self.after(50, self._update_plot)

    def _create_widgets(self) -> None:
        control = ttk.Frame(self)
        control.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control, text="Speed").pack(side=tk.LEFT, padx=4)
        ttk.Scale(control, from_=0.5, to=2.0, orient=tk.HORIZONTAL,
                  variable=self.speed).pack(side=tk.LEFT)

        ttk.Label(control, text="Arrhythmia").pack(side=tk.LEFT, padx=4)
        ttk.OptionMenu(control, self.pattern, self.pattern.get(),
                       *self.pattern_factories.keys(),
                       command=self._change_pattern).pack(side=tk.LEFT)

        ttk.Label(control, text="Highlight Lead").pack(side=tk.LEFT, padx=4)
        lead_options = [str(i) for i in range(1, 13)]
        ttk.OptionMenu(control, self.highlight, lead_options[0], *lead_options).pack(side=tk.LEFT)

    def _init_plot(self) -> None:
        matplotlib.use("Agg")  # Use non-interactive backend for embedding
        self.fig, axes = plt.subplots(3, 4, figsize=(10, 6))
        self.lines = []
        self.axes = axes.flatten()
        for idx, ax in enumerate(self.axes):
            line, = ax.plot([], [], lw=0.8, color="black")
            ax.set_ylim(-2, 2)
            ax.set_xlim(0, self.ecg.duration_sec)
            ax.set_title(f"Lead {idx+1}", fontsize=8)
            ax.axis("off")
            self.lines.append(line)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.fig.tight_layout()

    def _change_pattern(self, *_: str) -> None:
        factory = self.pattern_factories[self.pattern.get()]
        self.ecg.apply_pattern(factory())
        for line in self.lines:
            line.set_data([], [])
        self.canvas.draw()

    def _update_plot(self) -> None:
        dt = 0.05 * float(self.speed.get())
        samples = int(dt * self.ecg.sampling_rate)
        t, voltages = self.ecg.step(samples)

        for line, v in zip(self.lines, voltages):
            xdata = np.append(line.get_xdata(), t)
            ydata = np.append(line.get_ydata(), v)
            line.set_data(xdata, ydata)

        highlight = self.highlight.get()
        for i, line in enumerate(self.lines, start=1):
            if highlight == i:
                line.set_color("red")
                line.set_linewidth(1.5)
            else:
                line.set_color("black")
                line.set_linewidth(0.8)

        self.canvas.draw()
        self.after(50, self._update_plot)


def main() -> None:
    gui = ECGGui()
    gui.mainloop()


if __name__ == "__main__":
    main()
