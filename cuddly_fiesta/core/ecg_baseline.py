"""Simplified baseline helper used in tests."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from .grid_scaling import (
    SMALL_SQUARE_TIME_SEC,
    SMALL_SQUARE_VOLTAGE_MV,
    LARGE_SQUARE_TIME_SEC,
    LARGE_SQUARE_VOLTAGE_MV,
)

class ECGBaseline:
    def __init__(self, duration_sec: float = 10.0, sampling_rate: int = 1000):
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)
        self.time = np.linspace(0, duration_sec, self.n_samples, endpoint=False)
        self.baseline = np.zeros(self.n_samples)

    def _add_ecg_grid(self, ax):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        for x in np.arange(0, xlim[1] + SMALL_SQUARE_TIME_SEC, SMALL_SQUARE_TIME_SEC):
            ax.axvline(x, color="gray", linewidth=0.5, alpha=0.2)
        for y in np.arange(ylim[0], ylim[1] + SMALL_SQUARE_VOLTAGE_MV, SMALL_SQUARE_VOLTAGE_MV):
            ax.axhline(y, color="gray", linewidth=0.5, alpha=0.2)
        for x in np.arange(0, xlim[1] + LARGE_SQUARE_TIME_SEC, LARGE_SQUARE_TIME_SEC):
            ax.axvline(x, color="red", linewidth=1.0, alpha=0.3)
        for y in np.arange(ylim[0], ylim[1] + LARGE_SQUARE_VOLTAGE_MV, LARGE_SQUARE_VOLTAGE_MV):
            ax.axhline(y, color="red", linewidth=1.0, alpha=0.3)

    def get_baseline_data(self):
        return {
            "time": self.time,
            "baseline": self.baseline,
            "sampling_rate": self.sampling_rate,
            "duration_sec": self.duration_sec,
            "grid_specs": {
                "small_square_time_sec": SMALL_SQUARE_TIME_SEC,
                "small_square_voltage_mv": SMALL_SQUARE_VOLTAGE_MV,
                "large_square_time_sec": LARGE_SQUARE_TIME_SEC,
                "large_square_voltage_mv": LARGE_SQUARE_VOLTAGE_MV,
            },
        }
