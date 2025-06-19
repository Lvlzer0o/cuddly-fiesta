"""Lightweight ECG animation helper used in tests."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .core import ECGCore, MultiLeadECG


def animate_ecg(ecg_source, interval_ms: int = 40, show_grid: bool = False) -> FuncAnimation:
    """Animate an ``ECGCore`` or ``MultiLeadECG`` instance."""
    if isinstance(ecg_source, MultiLeadECG):
        voltage = list(ecg_source.leads.values())[0]
        time = ecg_source.time
    elif isinstance(ecg_source, ECGCore):
        voltage = ecg_source.voltage
        time = ecg_source.time
    else:
        raise TypeError("ecg_source must be ECGCore or MultiLeadECG")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, time[-1])
    ax.set_ylim(-2, 2)
    line, = ax.plot([], [], "k-")

    def update(frame):
        line.set_data(time[:frame], voltage[:frame])
        return line,

    frames = len(time)
    ani = FuncAnimation(fig, update, frames=frames, interval=interval_ms, blit=True)
    if not show_grid:
        ax.grid(False)
    return ani

__all__ = ["animate_ecg"]
