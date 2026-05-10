"""Canonical clinical ECG visualizer and export helpers."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, Iterable, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MultipleLocator
import numpy as np

from .core import ECGCore, MultiLeadECG
from .ui_registry import (
    DISPLAY_CONTROL_SPECS,
    DURATION,
    RHYTHM_REGISTRY,
    ParameterSpec,
    TARGET_FPS_OPTIONS,
    create_rhythm,
)


LEAD_ORDER = (
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
)

CLINICAL_12_LEAD_LAYOUT = (
    ("I", "aVR", "V1", "V4"),
    ("II", "aVL", "V2", "V5"),
    ("III", "aVF", "V3", "V6"),
)

ECG_PAPER = "#fffafa"
ECG_GRID_MAJOR = "#e7a6a6"
ECG_GRID_MINOR = "#f5d7d7"
ECG_TRACE = "#1d1d1d"
ECG_TRACE_FOCUS = "#b3002d"
PANEL_BG = "#eef2f4"


def _scaled_signal(signal: np.ndarray, gain: float) -> np.ndarray:
    return signal * (gain / 10.0)


def _signal_ylim(signals: Iterable[np.ndarray]) -> Tuple[float, float]:
    populated = [np.asarray(signal) for signal in signals if np.asarray(signal).size]
    if not populated:
        return -2.5, 2.5

    values = np.concatenate(populated)
    y_min = float(np.min(values))
    y_max = float(np.max(values))
    span = max(y_max - y_min, 1.0)
    padding = max(span * 0.1, 0.2)
    return y_min - padding, y_max + padding


def _remove_figure_axes(figure) -> None:
    for ax in list(figure.axes):
        ax.remove()
    suptitle = getattr(figure, "_suptitle", None)
    if suptitle is not None:
        suptitle.remove()
        figure._suptitle = None


def _ensure_axes(figure, view_mode: str):
    layout = getattr(figure, "_cuddly_layout", None)
    if view_mode == "12-lead":
        if layout != "12-lead" or len(figure.axes) != 12:
            _remove_figure_axes(figure)
            axes = figure.subplots(3, 4, sharex=True, sharey=True)
            figure._cuddly_layout = "12-lead"
            return axes
        return np.asarray(figure.axes, dtype=object).reshape(3, 4)

    if layout != "single" or len(figure.axes) != 1:
        _remove_figure_axes(figure)
        ax = figure.add_subplot(111)
        figure._cuddly_layout = "single"
        return ax
    return figure.axes[0]


def _set_trace(ax, time: np.ndarray, signal: np.ndarray, color: str, width: float):
    if ax.lines:
        line = ax.lines[0]
        line.set_data(time, signal)
        line.set_color(color)
        line.set_linewidth(width)
        for extra in ax.lines[1:]:
            extra.remove()
        return line
    return ax.plot(time, signal, color=color, linewidth=width)[0]


def _set_lead_label(ax, lead_name: str, color: str) -> None:
    label = getattr(ax, "_cuddly_lead_label", None)
    if label is None:
        label = ax.text(
            0.02,
            0.86,
            lead_name,
            transform=ax.transAxes,
            fontsize=10,
            fontweight="bold",
            color=color,
        )
        ax._cuddly_lead_label = label
        return
    label.set_text(lead_name)
    label.set_color(color)


def _style_ecg_axis(
    ax,
    duration_sec: float,
    gain: float,
    paper_speed: float,
    show_grid: bool,
) -> None:
    ax.set_facecolor(ECG_PAPER)
    ax.set_xlim(0, duration_sec)
    ax.set_yticks([])
    ax.tick_params(axis="x", labelsize=8, colors="#374151")
    ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_color("#c9c9c9")
        spine.set_linewidth(0.6)

    if show_grid:
        ax.xaxis.set_major_locator(MultipleLocator(5.0 / paper_speed))
        ax.xaxis.set_minor_locator(MultipleLocator(1.0 / paper_speed))
        ax.yaxis.set_major_locator(MultipleLocator(5.0 / gain))
        ax.yaxis.set_minor_locator(MultipleLocator(1.0 / gain))
        ax.grid(which="major", color=ECG_GRID_MAJOR, linewidth=0.55)
        ax.grid(which="minor", color=ECG_GRID_MINOR, linewidth=0.35)
    else:
        ax.grid(False, which="both")


def render_ecg_figure(
    ecg: ECGCore,
    view_mode: str = "single",
    lead_focus: str = "II",
    show_grid: bool = True,
    gain: float = 10,
    paper_speed: float = 25,
    figure=None,
    multi: Optional[MultiLeadECG] = None,
):
    """Render an ECGCore as a clinical single-lead or 12-lead figure."""
    if figure is None:
        figure = plt.figure(figsize=(13, 8 if view_mode == "12-lead" else 4.5))
    figure.patch.set_facecolor(ECG_PAPER)

    if multi is None:
        multi = MultiLeadECG.from_ecg(ecg)
    if view_mode == "12-lead":
        lead_signals = {
            lead_name: _scaled_signal(multi.get_lead(lead_name), gain)
            for lead_name in LEAD_ORDER
        }
        y_limits = _signal_ylim(lead_signals.values())
        axes = _ensure_axes(figure, "12-lead")
        for row_index, row in enumerate(CLINICAL_12_LEAD_LAYOUT):
            for col_index, lead_name in enumerate(row):
                ax = axes[row_index][col_index]
                trace_color = (
                    ECG_TRACE_FOCUS if lead_name == lead_focus else ECG_TRACE
                )
                line_width = 1.5 if lead_name == lead_focus else 0.9
                _set_trace(ax, ecg.time, lead_signals[lead_name], trace_color, line_width)
                _set_lead_label(ax, lead_name, trace_color)
                _style_ecg_axis(
                    ax, ecg.duration_sec, gain, paper_speed, show_grid
                )
                ax.set_ylim(*y_limits)
        figure.suptitle(
            f"12-lead ECG | {paper_speed:g} mm/s | {gain:g} mm/mV",
            fontsize=12,
            color="#111827",
        )
        figure.tight_layout(rect=(0, 0, 1, 0.96))
        return figure, axes

    lead_name = lead_focus if lead_focus in LEAD_ORDER else "II"
    signal = _scaled_signal(multi.get_lead(lead_name), gain)
    ax = _ensure_axes(figure, "single")
    _set_trace(ax, ecg.time, signal, ECG_TRACE_FOCUS, 1.2)
    _style_ecg_axis(ax, ecg.duration_sec, gain, paper_speed, show_grid)
    ax.set_ylim(*_signal_ylim((signal,)))
    ax.set_xlabel("Time (s)")
    ax.set_title(
        f"Lead {lead_name} | {paper_speed:g} mm/s | {gain:g} mm/mV",
        fontsize=12,
        color="#111827",
    )
    figure.tight_layout()
    return figure, ax


def export_ecg_image(
    ecg: ECGCore,
    path,
    view_mode: str = "12-lead",
    lead_focus: str = "II",
    show_grid: bool = True,
    gain: float = 10,
    paper_speed: float = 25,
) -> None:
    """Export a clinical ECG image."""
    figure, _ = render_ecg_figure(
        ecg,
        view_mode=view_mode,
        lead_focus=lead_focus,
        show_grid=show_grid,
        gain=gain,
        paper_speed=paper_speed,
    )
    figure.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(figure)


def export_ecg_csv(ecg: ECGCore, path) -> None:
    """Export event-synthesized 12-lead ECG data to CSV."""
    MultiLeadECG.from_ecg(ecg).export_to_csv(str(path))


class ECGVisualizer:
    """Tk application for clinical ECG inspection."""

    CONTROL_FIELDS = tuple(control.name for control in DISPLAY_CONTROL_SPECS)

    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("ECG Clinical Workstation")
        self.master.geometry("1280x820")

        self.sampling_rate = 1000
        self.current_ecg: Optional[ECGCore] = None
        self.current_multi: Optional[MultiLeadECG] = None
        self.animation_timer = None
        self.is_playing = False
        self.frame_index = 0
        self._plot_state: Optional[Tuple[str, str, bool, float, float]] = None
        self.current_rhythm_name = "Ready"
        self.current_duration_sec = 0.0

        self.rhythm_label_to_key = {
            spec.label: key for key, spec in RHYTHM_REGISTRY.items()
        }
        self.rhythm_var = tk.StringVar(
            value=RHYTHM_REGISTRY["normal_sinus"].label
        )
        self.param_vars: Dict[str, tk.Variable] = {}

        self.view_mode_var = tk.StringVar(value="12-lead")
        self.lead_focus_var = tk.StringVar(value="II")
        self.show_grid_var = tk.BooleanVar(value=True)
        self.gain_var = tk.DoubleVar(value=10.0)
        self.paper_speed_var = tk.DoubleVar(value=25.0)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.target_fps_var = tk.StringVar(value="60")
        self.play_button_var = tk.StringVar(value="Play")
        self.status_var = tk.StringVar(value="Ready")

        self._setup_style()
        self._setup_ui()
        self._build_parameter_controls()
        self.update_ecg()

    def _setup_style(self) -> None:
        self.master.configure(bg=PANEL_BG)
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=PANEL_BG)
        style.configure("TLabel", background=PANEL_BG, foreground="#1f2933")
        style.configure("TLabelframe", background=PANEL_BG)
        style.configure("TLabelframe.Label", background=PANEL_BG)
        style.configure("TButton", padding=(8, 4))

    def _setup_ui(self) -> None:
        main = ttk.Frame(self.master, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        self.control_frame = ttk.Frame(main, width=320)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        rhythm_frame = ttk.LabelFrame(self.control_frame, text="Rhythm")
        rhythm_frame.pack(fill=tk.X, pady=(0, 8))
        rhythm_menu = ttk.Combobox(
            rhythm_frame,
            textvariable=self.rhythm_var,
            values=[spec.label for spec in RHYTHM_REGISTRY.values()],
            state="readonly",
            width=30,
        )
        rhythm_menu.pack(fill=tk.X, padx=8, pady=8)
        rhythm_menu.bind("<<ComboboxSelected>>", self._on_rhythm_change)

        self.param_frame = ttk.LabelFrame(self.control_frame, text="Parameters")
        self.param_frame.pack(fill=tk.X, pady=(0, 8))

        display_frame = ttk.LabelFrame(self.control_frame, text="Display")
        display_frame.pack(fill=tk.X, pady=(0, 8))
        self._add_choice(
            display_frame,
            "View",
            self.view_mode_var,
            ("single", "12-lead"),
            self.update_plot,
        )
        self._add_choice(
            display_frame,
            "Lead focus",
            self.lead_focus_var,
            LEAD_ORDER,
            self.update_plot,
        )
        ttk.Checkbutton(
            display_frame,
            text="ECG grid",
            variable=self.show_grid_var,
            command=self.update_plot,
        ).pack(anchor=tk.W, padx=8, pady=4)
        self._add_spinbox(
            display_frame,
            "Gain",
            self.gain_var,
            5,
            20,
            1,
            "mm/mV",
            self.update_plot,
        )
        self._add_spinbox(
            display_frame,
            "Paper speed",
            self.paper_speed_var,
            12.5,
            50,
            12.5,
            "mm/s",
            self.update_plot,
        )
        self._add_spinbox(
            display_frame,
            "Playback",
            self.speed_var,
            0.25,
            4,
            0.25,
            "x",
            self._refresh_status,
        )
        self._add_choice(
            display_frame,
            "Target FPS",
            self.target_fps_var,
            TARGET_FPS_OPTIONS,
            self._refresh_status,
        )

        action_frame = ttk.LabelFrame(self.control_frame, text="Actions")
        action_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(
            action_frame,
            textvariable=self.play_button_var,
            command=self.toggle_play,
        ).pack(
            fill=tk.X, padx=8, pady=(8, 4)
        )
        ttk.Button(action_frame, text="Reset", command=self.reset).pack(
            fill=tk.X, padx=8, pady=4
        )
        ttk.Button(action_frame, text="Export Image", command=self.export_image).pack(
            fill=tk.X, padx=8, pady=4
        )
        ttk.Button(action_frame, text="Export CSV", command=self.export_csv).pack(
            fill=tk.X, padx=8, pady=(4, 8)
        )
        ttk.Label(self.control_frame, textvariable=self.status_var, wraplength=280).pack(
            fill=tk.X, pady=(4, 0)
        )

        self.figure = plt.Figure(figsize=(10, 7), facecolor=ECG_PAPER)
        self.canvas = FigureCanvasTkAgg(self.figure, master=main)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _current_key(self) -> str:
        return self.rhythm_label_to_key[self.rhythm_var.get()]

    def _current_parameter_values(self) -> Dict[str, Any]:
        values = {}
        spec = RHYTHM_REGISTRY[self._current_key()]
        for param in spec.parameters:
            values[param.name] = self.param_vars[param.name].get()
        return values

    def _build_parameter_controls(self) -> None:
        for child in self.param_frame.winfo_children():
            child.destroy()
        self.param_vars.clear()

        spec = RHYTHM_REGISTRY[self._current_key()]
        if not spec.parameters:
            ttk.Label(self.param_frame, text="No rhythm parameters").pack(
                anchor=tk.W, padx=8, pady=8
            )
            return

        for param in spec.parameters:
            if param.kind == "choice":
                variable = tk.StringVar(value=str(param.default))
                self.param_vars[param.name] = variable
                self._add_choice(
                    self.param_frame,
                    param.label,
                    variable,
                    param.options,
                    self.update_ecg,
                )
            else:
                variable = tk.DoubleVar(value=float(param.default))
                self.param_vars[param.name] = variable
                self._add_spinbox(
                    self.param_frame,
                    param.label,
                    variable,
                    param.minimum,
                    param.maximum,
                    param.step,
                    param.units,
                    self.update_ecg,
                )

    def _add_choice(
        self,
        parent,
        label: str,
        variable: tk.StringVar,
        options: Iterable[str],
        command,
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(row, text=label).pack(side=tk.LEFT)
        combo = ttk.Combobox(
            row, textvariable=variable, values=tuple(options), state="readonly", width=12
        )
        combo.pack(side=tk.RIGHT)
        if command:
            combo.bind("<<ComboboxSelected>>", lambda _event: command())

    def _add_spinbox(
        self,
        parent,
        label: str,
        variable: tk.Variable,
        minimum: Optional[float],
        maximum: Optional[float],
        step: Optional[float],
        units: str,
        command,
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, padx=8, pady=4)
        text = f"{label} ({units})" if units else label
        ttk.Label(row, text=text).pack(side=tk.LEFT)
        spin_kwargs = {
            "from_": minimum if minimum is not None else 0,
            "to": maximum if maximum is not None else 999,
            "increment": step if step is not None else 1,
            "textvariable": variable,
            "width": 8,
        }
        if command:
            spin_kwargs["command"] = command
        spin = ttk.Spinbox(row, **spin_kwargs)
        spin.pack(side=tk.RIGHT)
        if command:
            spin.bind("<Return>", lambda _event: command())
            spin.bind("<FocusOut>", lambda _event: command())

    def _on_rhythm_change(self, _event=None) -> None:
        self._build_parameter_controls()
        self.update_ecg()

    def update_ecg(self) -> None:
        try:
            values = self._current_parameter_values()
            duration_sec = float(values.get("duration_sec", DURATION.default))
            rhythm = create_rhythm(self._current_key(), values)
            ecg = ECGCore(duration_sec=duration_sec, sampling_rate=self.sampling_rate)
            rhythm.apply_to_ecg(ecg)
            self.current_ecg = ecg
            self.current_multi = MultiLeadECG.from_ecg(ecg)
            self.current_rhythm_name = rhythm.name
            self.current_duration_sec = duration_sec
            self.frame_index = 0
            self.update_plot()
        except Exception as exc:
            self.status_var.set(f"Could not generate rhythm: {exc}")
            messagebox.showerror("ECG generation failed", str(exc))

    def update_plot(self) -> None:
        if self.current_ecg is None:
            return
        state = self._requested_plot_state(self.view_mode_var.get())
        render_ecg_figure(
            self.current_ecg,
            view_mode=state[0],
            lead_focus=state[1],
            show_grid=state[2],
            gain=state[3],
            paper_speed=state[4],
            figure=self.figure,
            multi=self.current_multi,
        )
        self._plot_state = state
        self._refresh_status()
        self.canvas.draw_idle()

    def _requested_plot_state(
        self, view_mode: str
    ) -> Tuple[str, str, bool, float, float]:
        return (
            view_mode,
            self.lead_focus_var.get(),
            bool(self.show_grid_var.get()),
            float(self.gain_var.get()),
            float(self.paper_speed_var.get()),
        )

    def toggle_play(self) -> None:
        if self.is_playing:
            self._set_playing(False)
            if self.animation_timer is not None:
                self.master.after_cancel(self.animation_timer)
                self.animation_timer = None
            self._refresh_status()
            return
        self._set_playing(True)
        self._animate_once()
        self._refresh_status()

    def _set_playing(self, playing: bool) -> None:
        self.is_playing = playing
        if hasattr(self, "play_button_var"):
            self.play_button_var.set("Pause" if playing else "Play")

    def _var_value(self, name: str, default):
        variable = getattr(self, name, None)
        if variable is None:
            return default
        try:
            return variable.get()
        except (tk.TclError, TypeError, ValueError):
            return default

    def _status_text(self) -> str:
        rhythm = getattr(self, "current_rhythm_name", "Ready")
        duration = getattr(self, "current_duration_sec", 0.0)
        state = "Playing" if getattr(self, "is_playing", False) else "Stopped"
        plot_state = getattr(self, "_plot_state", None)
        if plot_state:
            view_mode, lead = plot_state[:2]
        else:
            view_mode = self._var_value("view_mode_var", "12-lead")
            lead = self._var_value("lead_focus_var", "II")
        try:
            speed = float(self._var_value("speed_var", 1.0))
        except (TypeError, ValueError):
            speed = 1.0
        fps = self._target_fps()
        return (
            f"{rhythm} | {duration:g}s | {state} | {view_mode} | "
            f"Lead {lead} | {speed:g}x | {fps} FPS"
        )

    def _refresh_status(self) -> None:
        if hasattr(self, "status_var"):
            self.status_var.set(self._status_text())

    def _target_fps(self) -> int:
        try:
            fps = int(float(self.target_fps_var.get()))
        except (AttributeError, tk.TclError, TypeError, ValueError):
            return 60
        if str(fps) not in TARGET_FPS_OPTIONS:
            return 60
        return fps

    def _animation_timing(self) -> Tuple[int, int]:
        try:
            playback_speed = float(self.speed_var.get())
        except (AttributeError, tk.TclError, TypeError, ValueError):
            playback_speed = 1.0
        playback_speed = max(0.01, playback_speed)
        target_fps = self._target_fps()
        delay = max(1, int(round(1000.0 / target_fps)))
        step = max(
            1,
            int(round(self.sampling_rate * playback_speed * delay / 1000.0)),
        )
        return step, delay

    def _animate_once(self) -> None:
        if not self.is_playing or self.current_ecg is None:
            return
        duration = self.current_ecg.duration_sec
        window = max(1.0, min(6.0, duration))
        step, delay = self._animation_timing()
        self.frame_index = (self.frame_index + step) % len(self.current_ecg.time)
        start_sec = self.frame_index / self.sampling_rate

        state = self._requested_plot_state("single")
        if self._plot_state != state or not self.figure.axes:
            render_ecg_figure(
                self.current_ecg,
                view_mode=state[0],
                lead_focus=state[1],
                show_grid=state[2],
                gain=state[3],
                paper_speed=state[4],
                figure=self.figure,
                multi=self.current_multi,
            )
            self._plot_state = state
        ax = self.figure.axes[0]
        ax.set_xlim(start_sec, min(duration, start_sec + window))
        self.canvas.draw_idle()
        self.animation_timer = self.master.after(delay, self._animate_once)

    def reset(self) -> None:
        self._set_playing(False)
        if self.animation_timer is not None:
            self.master.after_cancel(self.animation_timer)
            self.animation_timer = None
        self.frame_index = 0
        self.update_plot()

    def export_image(self) -> None:
        if self.current_ecg is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=(("PNG image", "*.png"), ("PDF", "*.pdf")),
        )
        if not path:
            return
        export_ecg_image(
            self.current_ecg,
            path,
            view_mode=self.view_mode_var.get(),
            lead_focus=self.lead_focus_var.get(),
            show_grid=self.show_grid_var.get(),
            gain=float(self.gain_var.get()),
            paper_speed=float(self.paper_speed_var.get()),
        )
        self.status_var.set(f"Image exported to {Path(path).name}")

    def export_csv(self) -> None:
        if self.current_ecg is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV", "*.csv"),),
        )
        if not path:
            return
        export_ecg_csv(self.current_ecg, path)
        self.status_var.set(f"CSV exported to {Path(path).name}")


def run_visualizer() -> None:
    """Run the canonical ECG visualizer application."""
    root = tk.Tk()
    ECGVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    run_visualizer()
