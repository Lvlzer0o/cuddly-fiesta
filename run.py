#!/usr/bin/env python3
"""
ECG Generator - Unified Entry Point
A comprehensive ECG waveform generator with clinical accuracy

This consolidated script combines all ECG generation, visualization, and UI functionality
into a single entry-point for ease of use.
"""

import argparse
import csv
import sys
import warnings
from abc import ABC, abstractmethod

from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, Union, Optional

# Visualization
import matplotlib
import matplotlib.pyplot as plt

import numpy as np

from matplotlib.animation import FuncAnimation
from scipy.stats import skewnorm

# GUI (optional - will work without tkinter)
try:
    import tkinter as tk
    from tkinter import ttk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    # Define placeholders for the imported modules
    tk = None
    ttk = None
    FigureCanvasTkAgg = None
    print("Note: Tkinter not available. GUI mode disabled.")


# ============================= CONSTANTS =============================

# Standard ECG parameters
PAPER_SPEED_MM_PER_SEC = 25
VOLTAGE_SCALE_MM_PER_MV = 10

# Grid dimensions
SMALL_SQUARE_TIME_SEC = 0.04  # 1 mm horizontally
SMALL_SQUARE_VOLTAGE_MV = 0.1  # 1 mm vertically
LARGE_SQUARE_TIME_SEC = 0.2  # 5 small squares
LARGE_SQUARE_VOLTAGE_MV = 0.5  # 5 small squares

# Clinical constants
REFERENCE_R_WAVE_MV = 1.0
GRID_TIME_STEP_MS = int(SMALL_SQUARE_TIME_SEC * 1000)
GRID_VOLTAGE_STEP_MV = SMALL_SQUARE_VOLTAGE_MV
FLOATING_POINT_TOLERANCE = 1e-6

# Pattern constants for missing variables
DEFAULT_PR_INTERVAL_SEC = 0.16
NORMAL_BEAT_ST_DURATION_SEC = 0.12


# ============================= CORE CLASSES =============================


class GridScaling:
    """Immutable grid scaling constants - NEVER modify these values."""

    PAPER_SPEED_MM_PER_SEC = PAPER_SPEED_MM_PER_SEC
    VOLTAGE_SCALE_MM_PER_MV = VOLTAGE_SCALE_MM_PER_MV
    SMALL_SQUARE_TIME_SEC = SMALL_SQUARE_TIME_SEC
    SMALL_SQUARE_VOLTAGE_MV = SMALL_SQUARE_VOLTAGE_MV
    LARGE_SQUARE_TIME_SEC = LARGE_SQUARE_TIME_SEC
    LARGE_SQUARE_VOLTAGE_MV = LARGE_SQUARE_VOLTAGE_MV

    @classmethod
    def validate_timing(cls, duration_ms: float) -> bool:
        """Validate timing aligns with grid units."""
        duration_sec = duration_ms / 1000.0
        remainder = duration_sec % cls.SMALL_SQUARE_TIME_SEC
        return (
            abs(remainder) < 1e-6
            or abs(remainder - cls.SMALL_SQUARE_TIME_SEC) < 1e-6
        )

    @classmethod
    def validate_amplitude(cls, amplitude_mv: float) -> bool:
        """Validate amplitude aligns with grid units."""
        remainder = amplitude_mv % cls.SMALL_SQUARE_VOLTAGE_MV
        return (
            abs(remainder) < 1e-6
            or abs(remainder - cls.SMALL_SQUARE_VOLTAGE_MV) < 1e-6
        )

    @classmethod
    def snap_to_grid_time(cls, duration_sec: float) -> float:
        """Snap duration to nearest grid unit."""
        return (
            round(duration_sec / cls.SMALL_SQUARE_TIME_SEC)
            * cls.SMALL_SQUARE_TIME_SEC
        )

    @classmethod
    def snap_to_grid_voltage(cls, amplitude_mv: float) -> float:
        """Snap amplitude to nearest grid unit."""
        return (
            round(amplitude_mv / cls.SMALL_SQUARE_VOLTAGE_MV)
            * cls.SMALL_SQUARE_VOLTAGE_MV
        )


class ECGBaseline:
    """ECG baseline generator with standard grid and calibration."""

    def __init__(self, duration_sec=10, sampling_rate=1000):
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)

        self.paper_speed_mm_per_sec = PAPER_SPEED_MM_PER_SEC
        self.voltage_scale_mm_per_mv = VOLTAGE_SCALE_MM_PER_MV
        self.small_square_time_sec = SMALL_SQUARE_TIME_SEC
        self.small_square_voltage_mv = SMALL_SQUARE_VOLTAGE_MV
        self.large_square_time_sec = LARGE_SQUARE_TIME_SEC
        self.large_square_voltage_mv = LARGE_SQUARE_VOLTAGE_MV

        self.time = np.linspace(
            0, duration_sec, self.n_samples, endpoint=False
        )
        self.baseline = self._generate_baseline()

    def _generate_baseline(self):
        """Generate isoelectric baseline with minimal physiologic variation."""
        baseline = np.zeros(self.n_samples)

        # Add minimal physiologic baseline drift (respiratory influence)
        respiratory_freq = 0.25  # Hz (15 breaths/min)
        respiratory_amplitude = 0.01  # mV (very subtle)
        respiratory_drift = respiratory_amplitude * np.sin(
            2 * np.pi * respiratory_freq * self.time
        )

        # Add very minimal random noise (electrode interface)
        noise_amplitude = 0.005  # mV
        noise = noise_amplitude * np.random.normal(0, 1, self.n_samples)

        return baseline + respiratory_drift + noise

    def _add_ecg_grid(self, ax):
        """Add standard ECG grid to the plot."""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Small squares (1mm) - light grid
        small_x_lines = np.arange(
            0, xlim[1] + self.small_square_time_sec, self.small_square_time_sec
        )
        small_y_lines = np.arange(
            ylim[0],
            ylim[1] + self.small_square_voltage_mv,
            self.small_square_voltage_mv,
        )

        for x in small_x_lines:
            ax.axvline(x, color="#FFB6C1", linewidth=0.5, alpha=0.7)

        for y in small_y_lines:
            ax.axhline(y, color="#FFB6C1", linewidth=0.5, alpha=0.7)

        # Large squares (5mm) - darker grid
        large_x_lines = np.arange(
            0, xlim[1] + self.large_square_time_sec, self.large_square_time_sec
        )
        large_y_lines = np.arange(
            ylim[0],
            ylim[1] + self.large_square_voltage_mv,
            self.large_square_voltage_mv,
        )

        for x in large_x_lines:
            ax.axvline(x, color="#FF69B4", linewidth=1.0, alpha=0.8)

        for y in large_y_lines:
            ax.axhline(y, color="#FF69B4", linewidth=1.0, alpha=0.8)

        # Emphasize zero line (isoelectric baseline)
        ax.axhline(0, color="red", linewidth=1.5, alpha=0.9)

    @staticmethod
    def _add_ecg_markers(ax):
        """Add clinical ECG markers for paper speed and voltage scale."""
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Add 25 mm/sec marker
        time_marker_x = xlim[1] - 1.0
        time_marker_y = ylim[0] + 0.1

        ax.annotate(
            "",
            xy=(time_marker_x, time_marker_y),
            xytext=(time_marker_x - 1.0, time_marker_y),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.5),
        )

        ax.text(
            time_marker_x - 0.5,
            time_marker_y - 0.15,
            "25 mm/sec",
            ha="center",
            va="top",
            fontsize=10,
            weight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9),
        )

        # Add 10 mm/mV marker
        voltage_marker_x = xlim[0] + 0.3
        voltage_marker_y = ylim[1] - 0.3

        ax.annotate(
            "",
            xy=(voltage_marker_x, voltage_marker_y),
            xytext=(voltage_marker_x, voltage_marker_y - 1.0),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.5),
        )

        ax.text(
            voltage_marker_x + 0.15,
            voltage_marker_y - 0.5,
            "10 mm/mV",
            ha="left",
            va="center",
            fontsize=10,
            weight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9),
        )

    @staticmethod
    def _add_calibration_pulse(ax):
        """Add standard 1mV calibration pulse - perfect rectangle."""
        cal_duration = 0.2  # seconds
        cal_amplitude = 1.0  # mV
        cal_start_time = 0.2  # Start 0.2 seconds from beginning

        cal_time_start = cal_start_time
        cal_time_end = cal_start_time + cal_duration

        # Draw calibration pulse with sharp vertical edges
        ax.plot(
            [cal_time_start, cal_time_start],
            [0, cal_amplitude],
            "k-",
            linewidth=2.5,
            solid_capstyle="butt",
        )
        ax.plot(
            [cal_time_start, cal_time_end],
            [cal_amplitude, cal_amplitude],
            "k-",
            linewidth=2.5,
            solid_capstyle="butt",
        )
        ax.plot(
            [cal_time_end, cal_time_end],
            [cal_amplitude, 0],
            "k-",
            linewidth=2.5,
            solid_capstyle="butt",
        )

        ax.annotate(
            "1 mV",
            xy=(cal_start_time + cal_duration / 2, cal_amplitude + 0.1),
            fontsize=9,
            ha="center",
            va="bottom",
            weight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.9),
        )

    def plot_with_grid(self, show_calibration=True, figure_size=(15, 8)):
        """Plot baseline with standard ECG grid."""
        fig, ax = plt.subplots(figsize=figure_size)

        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        ax.plot(
            self.time, self.baseline, "k-", linewidth=1.2, label="Baseline"
        )
        ax.set_xlim(0, self.duration_sec)
        ax.set_ylim(-2, 2)

        self._add_ecg_grid(ax)

        if show_calibration:
            self._add_calibration_pulse(ax)

        ax.set_xlabel("Time (seconds)", fontsize=12)
        ax.set_ylabel("Voltage (mV)", fontsize=12)
        ax.set_title(
            "ECG Baseline - Standard 25mm/sec, 10mm/mV",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(False)

        self._add_ecg_markers(ax)

        plt.tight_layout()
        return fig, ax

    def get_baseline_data(self):
        """Return baseline data for use in other modules."""
        return {
            "time": self.time,
            "baseline": self.baseline,
            "sampling_rate": self.sampling_rate,
            "duration_sec": self.duration_sec,
            "grid_specs": {
                "small_square_time_sec": self.small_square_time_sec,
                "small_square_voltage_mv": self.small_square_voltage_mv,
                "large_square_time_sec": self.large_square_time_sec,
                "large_square_voltage_mv": self.large_square_voltage_mv,
            },
        }


class ClinicalValidator:
    """Validates ECG waveform segments against clinical grid and timing constraints."""

    def __init__(self):
        self.small_square_time_ms = GRID_TIME_STEP_MS
        self.small_square_voltage_mv = GRID_VOLTAGE_STEP_MV
        self.large_square_time_ms = 5 * GRID_TIME_STEP_MS
        self.large_square_voltage_mv = 5 * GRID_VOLTAGE_STEP_MV

        # Clinical timing constraints (ms)
        self.timing_constraints = {
            "P_wave": {"min": 80, "max": 100, "target": 90},
            "PR_interval": {"min": 120, "max": 200, "target": 160},
            "QRS_complex": {"min": 80, "max": 120, "target": 100},
            "ST_segment": {"min": 80, "max": 120, "target": 100},
            "T_wave": {"min": 120, "max": 160, "target": 140},
            "QT_interval": {"min": 300, "max": 450, "target": 400},
            "U_wave": {"min": 60, "max": 110, "target": 80},
        }

        # Clinical amplitude constraints (relative to R wave = 1.0)
        self.amplitude_constraints = {
            "P_wave": {"min": 0.1, "max": 0.25, "target": 0.15},
            "Q_wave": {"min": 0.1, "max": 0.3, "target": 0.2},
            "R_wave": {"min": 0.8, "max": 1.0, "target": 1.0},
            "S_wave": {"min": 0.2, "max": 0.4, "target": 0.3},
            "T_wave": {"min": 0.1, "max": 0.5, "target": 0.25},
            "U_wave": {"min": 0.05, "max": 0.15, "target": 0.1},
            "QRS_complex": {"min": 0.5, "max": 1.5, "target": 1.0},
        }

    def snap_to_grid_time(self, time_ms):
        """Snap timing to nearest grid unit (40ms increments)."""
        return (
            round(time_ms / self.small_square_time_ms)
            * self.small_square_time_ms
        )

    def snap_to_grid_voltage(self, voltage_mv):
        """Snap voltage to nearest grid unit (0.1mV increments)."""
        return (
            round(voltage_mv / self.small_square_voltage_mv)
            * self.small_square_voltage_mv
        )

    def validate_timing(self, segment_name, duration_ms):
        """Validate segment timing against clinical constraints."""
        if segment_name not in self.timing_constraints:
            return (
                True,
                f"⚠️ No timing constraints defined for segment: {segment_name}",
            )

        constraints = self.timing_constraints[segment_name]
        snapped_duration = self.snap_to_grid_time(duration_ms)

        if constraints["min"] <= snapped_duration <= constraints["max"]:
            return (
                True,
                f"✅ {segment_name} timing: {snapped_duration}ms (valid)",
            )
        else:
            return (
                False,
                f"❌ {segment_name} timing: {snapped_duration}ms (outside {constraints['min']}-{constraints['max']}ms range)",
            )

    def validate_amplitude(self, segment_name, amplitude_mv):
        """Validate segment amplitude against clinical constraints."""
        if segment_name not in self.amplitude_constraints:
            return (
                True,
                f"⚠️ No amplitude constraints defined for segment: {segment_name}",
            )

        constraints = self.amplitude_constraints[segment_name]
        snapped_amplitude = self.snap_to_grid_voltage(amplitude_mv)

        if constraints["min"] <= snapped_amplitude <= constraints["max"]:
            return (
                True,
                f"✅ {segment_name} amplitude: {snapped_amplitude}mV (valid)",
            )
        else:
            return (
                False,
                f"❌ {segment_name} amplitude: {snapped_amplitude}mV (outside {constraints['min']}-{constraints['max']}mV range)",
            )

    def generate_grid_aligned_time(
        self, start_ms, duration_ms, sampling_rate=1000
    ):
        """Generate time array aligned to grid with specified duration."""
        snapped_start = self.snap_to_grid_time(start_ms)
        snapped_duration = self.snap_to_grid_time(duration_ms)

        # Make sure n_samples is an integer
        n_samples = int(snapped_duration * sampling_rate / 1000)
        time_array = np.linspace(
            snapped_start / 1000,
            (snapped_start + snapped_duration) / 1000,
            n_samples,
            endpoint=False,
        )

        return time_array, snapped_start, snapped_duration


class ECGCore:
    """Core ECG foundation with immutable grid scaling and baseline."""

    def __init__(self, duration_sec: float = 10, sampling_rate: int = 1000):
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)

        self.time = np.linspace(
            0, duration_sec, self.n_samples, endpoint=False
        )
        self.voltage = self._generate_baseline()
        self.segments_added = []
        self.grid = GridScaling()

    def _generate_baseline(self) -> np.ndarray:
        """Generate isoelectric baseline with minimal physiologic variation."""
        baseline = np.zeros(self.n_samples)

        respiratory_freq = 0.25
        respiratory_amplitude = 0.01
        respiratory_drift = respiratory_amplitude * np.sin(
            2 * np.pi * respiratory_freq * self.time
        )

        noise_amplitude = 0.005
        noise = noise_amplitude * np.random.normal(0, 1, self.n_samples)

        return baseline + respiratory_drift + noise

    def add_waveform_segment(
        self, segment: "WaveformSegment", start_time_sec: float
    ) -> None:
        """Add a waveform segment to the ECG while preserving grid scaling."""
        if not self.grid.validate_timing(start_time_sec * 1000):
            start_time_sec = self.grid.snap_to_grid_time(start_time_sec)
            warnings.warn(
                f"Start time snapped to grid: {start_time_sec:.3f} sec"
            )

        segment_time, segment_voltage = segment.generate(self.sampling_rate)

        self._validate_segment_grid_compliance(segment)

        start_idx = int(start_time_sec * self.sampling_rate)
        end_idx = start_idx + len(segment_voltage)

        if end_idx > self.n_samples:
            warnings.warn("Segment truncated to fit ECG duration")
            end_idx = self.n_samples
            segment_voltage = segment_voltage[: end_idx - start_idx]

        self.voltage[start_idx:end_idx] += segment_voltage

        self.segments_added.append(
            {
                "segment": segment,
                "start_time": start_time_sec,
                "duration": len(segment_voltage) / self.sampling_rate,
            }
        )

    def _validate_segment_grid_compliance(
        self, segment: "WaveformSegment"
    ) -> None:
        """Validate that segment respects grid scaling."""
        duration_ms = segment.duration_ms
        if not self.grid.validate_timing(duration_ms):
            raise ValueError(
                f"Segment duration {duration_ms}ms not aligned with grid units"
            )

        if hasattr(segment, "amplitude_mv"):
            if not self.grid.validate_amplitude(segment.amplitude_mv):
                warnings.warn(
                    f"Segment amplitude {segment.amplitude_mv}mV not aligned with grid units"
                )

    def plot_with_grid(
        self, show_calibration: bool = True, figure_size: Tuple = (15, 8)
    ):
        """Plot ECG with standard grid."""
        temp_baseline = ECGBaseline(self.duration_sec, self.sampling_rate)

        fig, ax = temp_baseline.plot_with_grid(show_calibration, figure_size)
        ax.clear()

        temp_baseline._add_ecg_grid(ax)
        ax.plot(self.time, self.voltage, "k-", linewidth=1.2, label="ECG")

        if show_calibration:
            temp_baseline._add_calibration_pulse(ax)

        ax.set_xlabel("Time (seconds)", fontsize=12)
        ax.set_ylabel("Voltage (mV)", fontsize=12)
        ax.set_title(
            "ECG with Grid Scaling Validation", fontsize=14, fontweight="bold"
        )
        ax.set_xlim(0, self.duration_sec)
        ax.set_ylim(-2, 2)
        ax.grid(False)

        temp_baseline._add_ecg_markers(ax)

        return fig, ax

    def validate_grid_integrity(self) -> bool:
        """Validate that all modifications preserve grid scaling."""
        print("🔍 Validating Grid Integrity...")

        valid = True

        time_resolution = 1.0 / self.sampling_rate
        grid_time_resolution = self.grid.SMALL_SQUARE_TIME_SEC / 10

        if time_resolution > grid_time_resolution:
            print(
                "⚠️  Warning: Sampling rate may be too low for grid precision"
            )
            print(
                f"   Current: {time_resolution*1000:.3f}ms, Recommended: <{grid_time_resolution*1000:.3f}ms"
            )

        for segment_info in self.segments_added:
            segment = segment_info["segment"]
            print(
                f"✅ Segment {segment.__class__.__name__}: Duration {segment.duration_ms}ms"
            )

        print(
            f"✅ Grid scaling validation complete. Total segments: {len(self.segments_added)}"
        )
        return valid


# ============================= WAVEFORM SEGMENTS =============================


class WaveformSegment(ABC):
    """Abstract base class for all ECG waveform segments."""

    def __init__(self, duration_ms: float, amplitude_mv: float):
        self.duration_ms = duration_ms
        self.amplitude_mv = amplitude_mv
        self.grid = GridScaling()
        self._validate_grid_alignment()

    def _validate_grid_alignment(self) -> None:
        """Ensure segment parameters align with grid."""
        if not self.grid.validate_timing(self.duration_ms):
            original = self.duration_ms
            self.duration_ms = (
                self.grid.snap_to_grid_time(self.duration_ms / 1000.0) * 1000.0
            )
            warnings.warn(
                f"Duration snapped to grid: {original}ms → {self.duration_ms}ms"
            )

    @abstractmethod
    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate waveform segment data."""
        pass


class PWave(WaveformSegment):
    """P-wave segment with clinical accuracy."""

    def __init__(self, amplitude_mv: float = 0.15, duration_ms: float = 100):
        if not (80 <= duration_ms <= 120):
            raise ValueError(
                f"P-wave duration {duration_ms}ms outside clinical range (80-120ms)"
            )

        if not (0.05 <= amplitude_mv <= 0.3):
            raise ValueError(
                f"P-wave amplitude {amplitude_mv}mV outside clinical range (0.05-0.3mV)"
            )

        super().__init__(duration_ms, amplitude_mv)

    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate P-wave using asymmetric double-Gaussian model."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(
            0, self.duration_ms / 1000.0, n_samples, endpoint=False
        )

        peak_time_1 = self.duration_ms * 0.3 / 1000.0
        peak_time_2 = self.duration_ms * 0.7 / 1000.0

        sigma_1 = self.duration_ms * 0.15 / 1000.0
        sigma_2 = self.duration_ms * 0.25 / 1000.0

        component_1 = (
            0.6
            * self.amplitude_mv
            * np.exp(-0.5 * ((time - peak_time_1) / sigma_1) ** 2)
        )
        component_2 = (
            0.4
            * self.amplitude_mv
            * np.exp(-0.5 * ((time - peak_time_2) / sigma_2) ** 2)
        )

        voltage = component_1 + component_2

        peak = np.max(np.abs(voltage))
        if peak > 0:
            voltage *= self.amplitude_mv / peak

        return time, voltage


class QRSComplex(WaveformSegment):
    """QRS complex with sharp triple-component morphology."""

    def __init__(
        self,
        r_amplitude_mv: float = 1.0,
        duration_ms: float = 100,
        q_ratio: float = 0.2,
        s_ratio: float = 0.3,
    ):
        if not (80 <= duration_ms <= 200):
            raise ValueError(
                f"QRS duration {duration_ms}ms outside clinical range (80-200ms)"
            )

        if not (0.5 <= r_amplitude_mv <= 3.0):
            raise ValueError(
                f"R amplitude {r_amplitude_mv}mV outside clinical range (0.5-3.0mV)"
            )

        super().__init__(duration_ms, r_amplitude_mv)
        self.q_ratio = q_ratio
        self.s_ratio = s_ratio

    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate QRS using triple-component sharp model."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(
            0, self.duration_ms / 1000.0, n_samples, endpoint=False
        )

        q_end = 0.3
        r_peak = 0.5
        # s_end variable is not used, removing it

        voltage = np.zeros(n_samples)

        # Q wave
        q_mask = time <= (q_end * self.duration_ms / 1000.0)
        voltage[q_mask] = (
            -self.q_ratio
            * self.amplitude_mv
            * (time[q_mask] / (q_end * self.duration_ms / 1000.0))
        )

        # R wave
        r_start = q_end * self.duration_ms / 1000.0
        r_peak_time = r_peak * self.duration_ms / 1000.0
        r_mask = (time > r_start) & (time <= r_peak_time)

        if np.any(r_mask):
            t_r = time[r_mask]
            voltage[r_mask] = (
                self.amplitude_mv * (t_r - r_start) / (r_peak_time - r_start)
                - self.q_ratio * self.amplitude_mv
            )

        # S wave
        s_start = r_peak_time
        s_mask = time > s_start

        if np.any(s_mask):
            t_s = time[s_mask]
            s_duration = (self.duration_ms / 1000.0) - s_start
            voltage[s_mask] = (
                self.amplitude_mv
                - (self.amplitude_mv + self.s_ratio * self.amplitude_mv)
                * (t_s - s_start)
                / s_duration
            )

        return time, voltage


class TWave(WaveformSegment):
    """T-wave segment representing ventricular repolarization."""

    def __init__(self, amplitude_mv: float = 0.25, duration_ms: float = 160):
        self._validator = ClinicalValidator()

        valid_timing, _ = self._validator.validate_timing(
            "T_wave", duration_ms
        )
        valid_amp, _ = self._validator.validate_amplitude(
            "T_wave", abs(amplitude_mv)
        )

        if not (valid_timing and valid_amp):
            raise ValueError(
                f"T-wave parameters outside clinical range: duration={duration_ms}ms amplitude={amplitude_mv}mV"
            )

        super().__init__(duration_ms, amplitude_mv)

    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate T-wave using skewed Gaussian morphology."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(
            0, self.duration_ms / 1000.0, n_samples, endpoint=False
        )

        t_norm = np.linspace(0, 1, n_samples)

        skew = 4 if self.amplitude_mv >= 0 else -4
        shape = skewnorm.pdf(t_norm, a=skew, loc=0.5, scale=0.2)
        if shape.max() != 0:
            shape /= shape.max()

        voltage = self.amplitude_mv * shape
        return time, voltage


class UWave(WaveformSegment):
    """U-wave segment following ventricular repolarization."""

    def __init__(self, amplitude_mv: float = 0.1, duration_ms: float = 80):
        self._validator = ClinicalValidator()

        valid_timing, _ = self._validator.validate_timing(
            "U_wave", duration_ms
        )
        valid_amp, _ = self._validator.validate_amplitude(
            "U_wave", abs(amplitude_mv)
        )

        if not (valid_timing and valid_amp):
            raise ValueError(
                f"U-wave parameters outside clinical range: duration={duration_ms}ms amplitude={amplitude_mv}mV"
            )

        super().__init__(duration_ms, amplitude_mv)

    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate U-wave using a simple narrow Gaussian."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(
            0, self.duration_ms / 1000.0, n_samples, endpoint=False
        )

        sigma = self.duration_ms / 1000.0 / 6
        center = self.duration_ms / 2000.0
        shape = np.exp(-0.5 * ((time - center) / sigma) ** 2)
        if shape.max() != 0:
            shape /= shape.max()

        voltage = self.amplitude_mv * shape
        return time, voltage


# ============================= ARRHYTHMIA PATTERNS =============================


class ArrhythmiaPattern(ABC):
    """Abstract base class for arrhythmia patterns - modular and swappable."""

    def __init__(self, name: str):
        self.name = name
        self.segments = []

    @abstractmethod
    def define_pattern(self) -> List[Dict]:
        """Define the pattern of segments and their timing."""
        pass

    def apply_to_ecg(self, ecg_core: ECGCore) -> None:
        """Apply this arrhythmia pattern to an ECG core."""
        pattern = self.define_pattern()

        for segment_def in pattern:
            segment = segment_def["segment"]
            start_time = segment_def["start_time_sec"]
            ecg_core.add_waveform_segment(segment, start_time)


class NormalSinusRhythm(ArrhythmiaPattern):
    """Normal sinus rhythm pattern - modular and swappable."""

    def __init__(self, heart_rate_bpm: int = 70):
        super().__init__("Normal Sinus Rhythm")

        if not (50 <= heart_rate_bpm <= 120):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside reasonable range (50-120 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.rr_interval_sec = 60.0 / heart_rate_bpm

    def define_pattern(self) -> list:
        """Define normal sinus rhythm pattern."""
        pattern = []

        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
        qrs_complex = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)
        t_wave = TWave(amplitude_mv=0.25, duration_ms=160)

        pr_interval_sec = 0.16
        qrs_start = pr_interval_sec

        pattern.append({"segment": p_wave, "start_time_sec": 0.0})

        pattern.append({"segment": qrs_complex, "start_time_sec": qrs_start})

        st_duration = 0.12
        t_wave_start = (
            qrs_start + qrs_complex.duration_ms / 1000.0 + st_duration
        )

        pattern.append({"segment": t_wave, "start_time_sec": t_wave_start})

        return pattern


class AtrialFibrillation(ArrhythmiaPattern):
    """Simple atrial fibrillation pattern with irregular RR intervals."""

    def __init__(self, heart_rate_bpm: int = 90, duration_sec: float = 3.0):
        super().__init__("Atrial Fibrillation")

        if not (60 <= heart_rate_bpm <= 150):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside range (60-150 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.duration_sec = duration_sec
        self._validator = ClinicalValidator()
        self.base_rr = 60.0 / heart_rate_bpm

    def define_pattern(self) -> list:
        pattern = []
        rng = np.random.default_rng(0)
        t = 0.0

        while t < self.duration_sec:
            qrs = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)
            qrs_start = self._validator.snap_to_grid_time(t * 1000) / 1000.0
            pattern.append({"segment": qrs, "start_time_sec": qrs_start})

            tw_start = qrs_start + qrs.duration_ms / 1000.0 + 0.12
            t_wave = TWave(amplitude_mv=0.25, duration_ms=160)
            tw_start = (
                self._validator.snap_to_grid_time(tw_start * 1000) / 1000.0
            )
            pattern.append({"segment": t_wave, "start_time_sec": tw_start})

            uw_start = tw_start + t_wave.duration_ms / 1000.0 + 0.04
            u_wave = UWave(amplitude_mv=0.1, duration_ms=80)
            uw_start = (
                self._validator.snap_to_grid_time(uw_start * 1000) / 1000.0
            )
            pattern.append({"segment": u_wave, "start_time_sec": uw_start})

            rr = self.base_rr + rng.uniform(
                -0.3 * self.base_rr, 0.3 * self.base_rr
            )
            t += rr

        return pattern


class VentricularTachycardia(ArrhythmiaPattern):
    """Rapid ventricular tachycardia pattern."""

    def __init__(self, heart_rate_bpm: int = 160, duration_sec: float = 3.0):
        super().__init__("Ventricular Tachycardia")

        if not (120 <= heart_rate_bpm <= 250):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside range (120-250 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.duration_sec = duration_sec
        self._validator = ClinicalValidator()
        self.rr_interval = 60.0 / heart_rate_bpm

    def define_pattern(self) -> list:
        pattern = []
        t = 0.0

        while t < self.duration_sec:
            qrs = QRSComplex(
                r_amplitude_mv=1.2, duration_ms=160, q_ratio=0.1, s_ratio=0.1
            )
            qrs_start = self._validator.snap_to_grid_time(t * 1000) / 1000.0
            pattern.append({"segment": qrs, "start_time_sec": qrs_start})

            tw_start = qrs_start + qrs.duration_ms / 1000.0 + 0.08
            t_wave = TWave(amplitude_mv=-0.2, duration_ms=160)
            tw_start = (
                self._validator.snap_to_grid_time(tw_start * 1000) / 1000.0
            )
            pattern.append({"segment": t_wave, "start_time_sec": tw_start})

            t += self.rr_interval

        return pattern


# ============================= MULTI-LEAD ECG =============================


class MultiLeadECG:
    """Container for 12 ECG lead signals.

    Each lead is produced by projecting the heart's electrical vector onto
    an orientation that matches the anatomical placement of the electrodes.
    Lead directions are described using spherical angles ``theta`` (azimuth in
    the frontal plane) and ``phi`` (elevation out of that plane).  The
    :py:meth:`_vector_from_angles` helper converts these angles into unit
    Cartesian vectors which are then used to scale the base ECG signal.
    """

    def __init__(self, leads: Dict[str, np.ndarray], sampling_rate: int) -> None:
        """Initialize with pre-computed lead signals.

        Parameters
        ----------
        leads:
            Mapping of lead name to voltage time series.
        sampling_rate:
            Samples per second for all signals.
        """

        self.leads = leads
        self.sampling_rate = sampling_rate
        self.n_samples = len(next(iter(leads.values())))
        self.time = np.arange(self.n_samples) / sampling_rate
        self.duration_sec = self.n_samples / sampling_rate
        self._baseline_grid_helper = None

    # ------------------------------------------------------------------
    # Legacy construction helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _vector_from_angles(theta_deg: float, phi_deg: float) -> np.ndarray:
        """Convert spherical angles to a unit Cartesian vector.

        ``theta_deg`` is the azimuth within the frontal plane and
        ``phi_deg`` is the elevation angle relative to that plane.  This
        matches the common anatomical description of lead axes.
        """
        theta = np.radians(theta_deg)
        phi = np.radians(phi_deg)
        x = np.cos(phi) * np.cos(theta)
        y = np.sin(phi)
        z = np.cos(phi) * np.sin(theta)
        vec = np.array([x, y, z], dtype=float)
        norm = np.linalg.norm(vec)
        return vec / norm if norm != 0 else vec

    @classmethod
    def from_ecg(
        cls,
        ecg: ECGCore,
        axis_theta_deg: float = 60.0,
        axis_phi_deg: float = 0.0,
        morphology: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> "MultiLeadECG":
        """Create ``MultiLeadECG`` from an ``ECGCore`` instance.

        ``axis_theta_deg`` and ``axis_phi_deg`` describe the mean electrical
        axis of the heart.  Each lead is generated by projecting the base ECG
        signal onto its orientation vector and scaling by the resulting dot
        product.
        """

        base = ecg.voltage
        heart_vec = cls._vector_from_angles(axis_theta_deg, axis_phi_deg)

        def lead_vector(theta: float, phi: float = 0.0) -> np.ndarray:
            return cls._vector_from_angles(theta, phi)

        # Mapping of lead name to its orientation vector.  Limb and augmented
        # leads lie in the frontal plane (``phi=0``) and follow the standard
        # hexaxial reference angles.  Precordial leads are approximated on the
        # horizontal plane sweeping from the right (V1) to the left side of the
        # chest (V6).
        vectors: Dict[str, np.ndarray] = {
            "I": lead_vector(0),      # RA → LA
            "II": lead_vector(60),    # RA → LL
            "III": lead_vector(120),  # LA → LL
            "aVR": lead_vector(-150), # RA vs (LA+LL)
            "aVL": lead_vector(-30),  # LA vs (RA+LL)
            "aVF": lead_vector(90),   # LL vs (RA+LA)
            # Precordial leads
            "V1": lead_vector(110),   # Right sternal border
            "V2": lead_vector(100),
            "V3": lead_vector(75),
            "V4": lead_vector(60),
            "V5": lead_vector(30),
            "V6": lead_vector(0),
        }

        leads: Dict[str, np.ndarray] = {}
        lead_scales: Dict[str, float] = {}
        for name, vec in vectors.items():
            scale = float(np.dot(heart_vec, vec))
            lead_scales[name] = scale
            leads[name] = base * scale

        morphology = morphology or {}
        for info in ecg.segments_added:
            segment = info["segment"]
            start_idx = int(info["start_time"] * ecg.sampling_rate)
            seg_time, seg_base = segment.generate(ecg.sampling_rate)
            seg_len = len(seg_base)

            for name in vectors.keys():
                morph = morphology.get(name, {})
                scale = lead_scales[name]
                diff = None

                if isinstance(segment, PWave):
                    p_scale = morph.get("P", 1.0)
                    if p_scale != 1.0:
                        new_seg = PWave(
                            amplitude_mv=segment.amplitude_mv * p_scale,
                            duration_ms=segment.duration_ms,
                        )
                        _, seg_new = new_seg.generate(ecg.sampling_rate)
                        diff = (seg_new - seg_base) * scale

                elif isinstance(segment, QRSComplex):
                    qrs_cfg = morph.get("QRS", {})
                    if qrs_cfg:
                        r_scale = qrs_cfg.get("r_scale", 1.0)
                        q_ratio = qrs_cfg.get("q_ratio", segment.q_ratio)
                        s_ratio = qrs_cfg.get("s_ratio", segment.s_ratio)
                        if (
                            r_scale != 1.0
                            or q_ratio != segment.q_ratio
                            or s_ratio != segment.s_ratio
                        ):
                            new_seg = QRSComplex(
                                r_amplitude_mv=segment.amplitude_mv * r_scale,
                                duration_ms=segment.duration_ms,
                                q_ratio=q_ratio,
                                s_ratio=s_ratio,
                            )
                            _, seg_new = new_seg.generate(ecg.sampling_rate)
                            diff = (seg_new - seg_base) * scale

                elif isinstance(segment, TWave):
                    t_scale = morph.get("T", 1.0)
                    if t_scale != 1.0:
                        new_seg = TWave(
                            amplitude_mv=segment.amplitude_mv * t_scale,
                            duration_ms=segment.duration_ms,
                        )
                        _, seg_new = new_seg.generate(ecg.sampling_rate)
                        diff = (seg_new - seg_base) * scale

                if diff is not None:
                    end_idx = min(start_idx + seg_len, len(leads[name]))
                    seg_slice = slice(start_idx, end_idx)
                    leads[name][seg_slice] += diff[: end_idx - start_idx]

        return cls(leads, ecg.sampling_rate)

    @staticmethod
    def _vector_from_angles(theta_deg: float, phi_deg: float) -> np.ndarray:
        """Convert spherical angles to a unit Cartesian vector.

        This duplicate helper is kept for backward compatibility with code
        that imported it from ``MultiLeadECG`` prior to refactoring.
        """
        theta = np.radians(theta_deg)
        phi = np.radians(phi_deg)
        x = np.cos(phi) * np.cos(theta)
        y = np.sin(phi)
        z = np.cos(phi) * np.sin(theta)
        vec = np.array([x, y, z], dtype=float)
        norm = np.linalg.norm(vec)
        return vec / norm if norm != 0 else vec


    def get_lead(self, name: str):
        """Return the voltage array for the specified lead."""
        return self.leads[name]

    def plot_all_leads(
        self, figure_size: Tuple[int, int] = (12, 8), with_grid: bool = False
    ):
        """Plot all 12 leads in a 4x3 grid."""
        fig, axes = plt.subplots(
            4, 3, figsize=figure_size, sharex=True, sharey=True
        )
        order = [
            "I", "II", "III",
            "aVR", "aVL", "aVF",
            "V1", "V2", "V3",
            "V4", "V5", "V6"
        ]

        # Initialize the grid helper if needed
        if with_grid and self._baseline_grid_helper is None:
            self._baseline_grid_helper = ECGBaseline(
                duration_sec=self.duration_sec,
                sampling_rate=self.sampling_rate
            )

        for ax, name in zip(axes.ravel(), order):
            ax.plot(self.time, self.leads[name], "k", linewidth=1)
            ax.set_title(name)
            ax.set_xlim(0, self.duration_sec)
            ax.set_ylim(-2, 2)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axhline(0, color="gray", linewidth=0.5)
            if with_grid and self._baseline_grid_helper is not None:
                self._baseline_grid_helper._add_ecg_grid(ax)

        fig.suptitle("12-Lead ECG", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return fig, axes

    def save_plot(
        self,
        path: str,
        figure_size: Tuple[int, int] = (12, 8),
        with_grid: bool = False,
    ) -> None:
        """Save the multi-lead plot to path."""
        fig, _ = self.plot_all_leads(
            figure_size=figure_size, with_grid=with_grid
        )
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def export_to_csv(self, path: str) -> None:
        """Export all leads to a CSV file for analysis."""
        order = [
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
        with open(path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["time"] + order)
            for idx, t in enumerate(self.time):
                row = [t] + [self.leads[name][idx] for name in order]
                writer.writerow(row)


# ============================= ECG ANIMATION =============================


def _animate_single_lead(ecg: ECGCore, interval_ms: int) -> FuncAnimation:
    """Animate a single-lead ECG."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, ecg.duration_sec)
    ax.set_ylim(-2, 2)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Voltage (mV)")
    ax.set_title("ECG Animation")
    ax.axhline(0, color="gray", linewidth=0.5)

    (line,) = ax.plot([], [], "k", linewidth=1)
    time = ecg.time
    voltage = ecg.voltage

    def init():
        line.set_data([], [])
        return (line,)

    def update(frame):
        line.set_data(time[:frame], voltage[:frame])
        return (line,)

    return FuncAnimation(
        fig,
        update,
        frames=len(time),
        init_func=init,
        interval=interval_ms,
        blit=True,
    )


def _animate_multi_lead(
    multi: MultiLeadECG, interval_ms: int
) -> FuncAnimation:
    """Animate all 12 leads in a 4x3 grid."""
    order = [
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
    fig, axes = plt.subplots(4, 3, figsize=(12, 8), sharex=True, sharey=True)
    lines = []
    for ax, name in zip(axes.ravel(), order):
        ax.set_xlim(0, multi.duration_sec)
        ax.set_ylim(-2, 2)
        ax.set_title(name)
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.set_xticks([])
        ax.set_yticks([])
        (line,) = ax.plot([], [], "k", linewidth=1)
        lines.append(line)

    time = multi.time
    leads = [multi.leads[name] for name in order]

    def init():
        for ln in lines:
            ln.set_data([], [])
        return lines

    def update(frame):
        for ln, data in zip(lines, leads):
            ln.set_data(time[:frame], data[:frame])
        return lines

    fig.suptitle("Real-time 12-Lead ECG", fontsize=14, fontweight="bold")
    plt.tight_layout()

    return FuncAnimation(
        fig,
        update,
        frames=len(time),
        init_func=init,
        interval=interval_ms,
        blit=True,
    )


def animate_ecg(
    ecg_source: Union[ECGCore, MultiLeadECG], interval_ms: int = 40
) -> FuncAnimation:
    """Animate ECG data from ECGCore or MultiLeadECG."""
    if isinstance(ecg_source, MultiLeadECG):
        return _animate_multi_lead(ecg_source, interval_ms)
    elif isinstance(ecg_source, ECGCore):
        return _animate_single_lead(ecg_source, interval_ms)
    else:
        raise TypeError("ecg_source must be ECGCore or MultiLeadECG")


# ============================= GUI APPLICATION =============================

if HAS_TKINTER:

    class ECGGui:
        """Display a MultiLeadECG in a Tkinter window with basic controls."""

        def __init__(self, master: tk.Tk):
            self.master = master
            master.title("ECG Generator GUI")

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

        def _create_figure(self) -> None:
            self.fig, self.axes = plt.subplots(
                4, 3, figsize=(12, 8), sharex=True, sharey=True
            )
            plt.tight_layout()
            if FigureCanvasTkAgg is None:
                raise RuntimeError("Tkinter backend is not available")
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        def _setup_ecg(self) -> None:
            pattern_cls = self.pattern_classes[self.pattern_name.get()]
            pattern = pattern_cls()
            ecg = ECGCore(duration_sec=self.ecg_length_sec, sampling_rate=1000)
            pattern.apply_to_ecg(ecg)
            self.multi = MultiLeadECG.from_ecg(ecg)

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

            self.lines = [
                ax.plot([], [], "k", linewidth=1)[0]
                for ax in self.axes.ravel()
            ]
            self.frame_idx = 0
            self._apply_highlight()
            self.canvas.draw()

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
            """Periodically updates the ECG plot to create an animation."""
            if not self.running:
                return
            base_samples_per_update = (1000 * self.interval_ms) / 1000.0
            step = max(
                1, int(base_samples_per_update * self.playback_speed.get())
            )
            self.frame_idx = (self.frame_idx + step) % len(self.time)
            for ln, data in zip(self.lines, self.leads):
                ln.set_data(
                    self.time[: self.frame_idx], data[: self.frame_idx]
                )
            self.canvas.draw_idle()
            self.master.after(self.interval_ms, self._update_plot)


# ============================= MAIN FUNCTIONS =============================


def demo_baseline():
    """Demonstrate ECG baseline with grid and calibration."""
    print("Generating ECG Baseline...")

    ecg_baseline = ECGBaseline(duration_sec=10, sampling_rate=1000)
    fig, ax = ecg_baseline.plot_with_grid(show_calibration=True)

    info_text = (
        "Standard ECG Grid:\n"
        "• Small squares: 0.04 sec × 0.1 mV\n"
        "• Large squares: 0.2 sec × 0.5 mV"
    )

    ax.text(
        0.02,
        0.98,
        info_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round,pad=0.4", facecolor="lightyellow", alpha=0.8
        ),
    )

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    plt.savefig(
        output_dir / "ecg_baseline_demo.png", dpi=300, bbox_inches="tight"
    )
    plt.close()

    print("✅ Baseline demo saved as 'output/ecg_baseline_demo.png'")


def demo_single_beat():
    """Demonstrate a single heartbeat with all components."""
    print("Generating single heartbeat...")

    ecg = ECGCore(duration_sec=2, sampling_rate=1000)

    # Add single heartbeat
    p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
    qrs = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)
    t_wave = TWave(amplitude_mv=0.25, duration_ms=160)

    ecg.add_waveform_segment(p_wave, start_time_sec=0.5)
    ecg.add_waveform_segment(qrs, start_time_sec=0.66)  # PR interval of 160ms
    ecg.add_waveform_segment(
        t_wave, start_time_sec=0.88
    )  # ST segment of 120ms

    fig, ax = ecg.plot_with_grid()
    ax.set_title("Single Heartbeat Demo", fontsize=14, fontweight="bold")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    plt.savefig(
        output_dir / "single_heartbeat_demo.png", dpi=300, bbox_inches="tight"
    )
    plt.close()

    print(
        "✅ Single heartbeat demo saved as 'output/single_heartbeat_demo.png'"
    )


def demo_arrhythmias():
    """Demonstrate different arrhythmia patterns."""
    print("Generating arrhythmia demonstrations...")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    patterns = [
        ("Normal Sinus Rhythm", NormalSinusRhythm(heart_rate_bpm=70)),
        ("Atrial Fibrillation", AtrialFibrillation(heart_rate_bpm=90)),
        (
            "Ventricular Tachycardia",
            VentricularTachycardia(heart_rate_bpm=160),
        ),
    ]

    for name, pattern in patterns:
        ecg = ECGCore(duration_sec=3, sampling_rate=1000)
        pattern.apply_to_ecg(ecg)

        fig, ax = ecg.plot_with_grid(show_calibration=False)
        ax.set_title(f"{name} Demo", fontsize=14, fontweight="bold")

        filename = name.lower().replace(" ", "_") + "_demo.png"
        plt.savefig(output_dir / filename, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"✅ {name} demo saved as 'output/{filename}'")


def demo_12_lead():
    """Demonstrate 12-lead ECG display."""
    print("Generating 12-lead ECG...")

    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    pattern = NormalSinusRhythm(heart_rate_bpm=70)
    pattern.apply_to_ecg(ecg)

    multi = MultiLeadECG.from_ecg(ecg)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    multi.save_plot(str(output_dir / "12_lead_ecg_demo.png"), with_grid=True)
    multi.export_to_csv(str(output_dir / "12_lead_ecg_data.csv"))

    print("✅ 12-lead ECG saved as 'output/12_lead_ecg_demo.png'")
    print("✅ ECG data exported to 'output/12_lead_ecg_data.csv'")


def run_animation(multi_lead=False, interval_ms=40):
    """Run real-time ECG animation."""
    print("Starting ECG animation...")
    print("Close the window to exit.")

    ecg = ECGCore(duration_sec=5, sampling_rate=1000)
    pattern = NormalSinusRhythm(heart_rate_bpm=70)

    # Apply pattern multiple times for continuous display
    for i in range(5):
        pattern_copy = NormalSinusRhythm(heart_rate_bpm=70)
        for segment_def in pattern_copy.define_pattern():
            segment = segment_def["segment"]
            start_time = (
                segment_def["start_time_sec"] + i * pattern.rr_interval_sec
            )
            if start_time < ecg.duration_sec:
                ecg.add_waveform_segment(segment, start_time)

    if multi_lead:
        source = MultiLeadECG.from_ecg(ecg)
    else:
        source = ecg

    # Create and show the animation (but don't return it)
    animate_ecg(source, interval_ms=interval_ms)
    plt.show()


def run_gui():
    """Run the Tkinter GUI application."""
    if not HAS_TKINTER:
        print("Error: Tkinter is not available. Cannot run GUI mode.")
        print("Please install tkinter or use other demo modes.")
        return

    print("Starting ECG GUI...")
    print("Close the window to exit.")

    matplotlib.use("TkAgg")
    root = tk.Tk()
    ECGGui(root)
    root.mainloop()


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description="ECG Generator - Comprehensive ECG waveform generator with clinical accuracy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --demo baseline      # Generate baseline with grid
  %(prog)s --demo single        # Generate single heartbeat
  %(prog)s --demo arrhythmias   # Generate arrhythmia examples
  %(prog)s --demo 12lead        # Generate 12-lead ECG
  %(prog)s --demo all           # Generate all demos
  
  %(prog)s --animate            # Run single-lead animation
  %(prog)s --animate --multi    # Run 12-lead animation
  
  %(prog)s --gui                # Run interactive GUI (requires tkinter)
        """,
    )

    parser.add_argument(
        "--demo",
        choices=["baseline", "single", "arrhythmias", "12lead", "all"],
        help="Generate demonstration plots",
    )

    parser.add_argument(
        "--animate", action="store_true", help="Run real-time ECG animation"
    )

    parser.add_argument(
        "--multi",
        action="store_true",
        help="Use 12-lead display for animation",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=40,
        help="Animation interval in milliseconds (default: 40)",
    )

    parser.add_argument(
        "--gui", action="store_true", help="Run interactive GUI application"
    )

    args = parser.parse_args()

    # Default action if no arguments
    if not any([args.demo, args.animate, args.gui]):
        print("ECG Generator - No action specified")
        print("Run with --help for usage information")
        print("\nQuick start:")
        print("  python run.py --demo all     # Generate all demos")
        print("  python run.py --animate      # Run animation")
        print("  python run.py --gui          # Run GUI")
        sys.exit(0)

    # Execute requested actions
    if args.demo:
        if args.demo == "baseline" or args.demo == "all":
            demo_baseline()
        if args.demo == "single" or args.demo == "all":
            demo_single_beat()
        if args.demo == "arrhythmias" or args.demo == "all":
            demo_arrhythmias()
        if args.demo == "12lead" or args.demo == "all":
            demo_12_lead()

        if args.demo == "all":
            print("\n✅ All demonstrations completed!")
            print("Check the 'output' directory for generated files.")

    if args.animate:
        run_animation(multi_lead=args.multi, interval_ms=args.interval)

    if args.gui:
        run_gui()


if __name__ == "__main__":
    main()
