"""
Example Waveform Segments
Demonstrates modular waveform segments that respect grid scaling.

This module provides various ECG waveform segments that can be used to create
arrhythmia patterns while ensuring clinical accuracy and grid integrity.
It includes:
- P-wave, QRS complex, T-wave, and U-wave segments
- Lead-specific waveform classes
- Arrhythmia patterns like Normal Sinus Rhythm, Atrial Fibrillation, etc.

The segments can be easily swapped and validated against clinical parameters.
The ECGCore class manages these segments and ensures they fit within a defined
grid, allowing for plug-and-play usage in ECG simulations.

This module is designed to be used independently of the main demo script
and can be imported and utilized in other projects where ECG waveform
generation is required.

The segments are designed to:
- Maintain grid scaling (no distortion)
- Allow easy swapping of arrhythmia patterns
- Validate clinical parameters for accuracy

Note: This module requires the `ClinicalValidator` and `ECGCore` classes
from the `cuddly_fiesta` package to function correctly.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import skewnorm

from .clinical_validator import ClinicalValidator
from .ecg_core import ArrhythmiaPattern, ECGCore, WaveformSegment

__all__ = [
    "PWave",
    "QRSComplex",
    "TWave",
    "UWave",
    "FibrillationWave",
    "LeadFibrillationWave",
    "LeadQRSComplex",
    "LeadTWave",
    "NormalSinusRhythm",
    "SinusBradycardia",
    "SinusTachycardia",
    "AtrialFibrillation",
    "VentricularTachycardia",
    "PrematureVentricularContraction",
    "SecondDegreeAVBlock",
    "AtrialFlutter",
    "VentricularFibrillation",
    "PulselessElectricalActivity",
]

logger = logging.getLogger(__name__)

# Default timing constants used by some arrhythmia patterns.  These values
# originally lived in ``run.py`` but are duplicated here so the module can be
# used independently of the demo script.
DEFAULT_PR_INTERVAL_SEC = 0.16
NORMAL_BEAT_ST_DURATION_SEC = 0.12


class PWave(WaveformSegment):
    """P-wave segment with clinical accuracy."""

    def __init__(self, amplitude_mv: float = 0.15, duration_ms: float = 100):
        """
        Initialize P-wave.

        Clinical Parameters:
        - Duration: 80-100 ms (normal atrial depolarization)
        - Amplitude: 0.1-0.25 mV (10-25% of R wave)
        """
        # Validate clinical ranges
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

        # Asymmetric double-Gaussian for realistic P-wave
        # Early component: Right atrial depolarization (faster)
        # Late component: Left atrial depolarization (slower)

        peak_time_1 = self.duration_ms * 0.3 / 1000.0  # Right atrium peak
        peak_time_2 = self.duration_ms * 0.7 / 1000.0  # Left atrium peak

        sigma_1 = self.duration_ms * 0.15 / 1000.0  # Faster rise
        sigma_2 = self.duration_ms * 0.25 / 1000.0  # Slower fall

        # Generate components
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

        # Scale to ensure the peak amplitude matches the configured value
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
        """
        Initialize QRS complex.

        Clinical Parameters:
        - Duration: 80-200 ms (normal to prolonged ventricular depolarization)
        - R amplitude: Reference (1.0 mV typical)
        - Q ratio: Q wave depth as fraction of R (0.1-0.3)
        - S ratio: S wave depth as fraction of R (0.2-0.4)
        """
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

        # Define component timing (sharp transitions)
        q_end = 0.3  # Q wave ends at 30% of QRS duration
        r_peak = 0.5  # R wave peaks at 50% of QRS duration

        voltage = np.zeros(n_samples)

        # Q wave (sharp downward deflection)
        q_mask = time <= (q_end * self.duration_ms / 1000.0)
        voltage[q_mask] = (
            -self.q_ratio
            * self.amplitude_mv
            * (time[q_mask] / (q_end * self.duration_ms / 1000.0))
        )

        # R wave (sharp upward peak)
        r_start = q_end * self.duration_ms / 1000.0
        r_peak_time = r_peak * self.duration_ms / 1000.0
        r_mask = (time > r_start) & (time <= r_peak_time)

        if np.any(r_mask):
            t_r = time[r_mask]
            # Sharp rise to peak
            voltage[r_mask] = (
                self.amplitude_mv * (t_r - r_start) / (r_peak_time - r_start)
                - self.q_ratio * self.amplitude_mv
            )

        # S wave (sharp downward deflection)
        s_start = r_peak_time
        s_mask = time > s_start

        if np.any(s_mask):
            t_s = time[s_mask]
            # Sharp fall to S depth
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
        """Initialize T-wave with clinical validation."""
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

        # Normalized time for morphology generation
        t_norm = np.linspace(0, 1, n_samples)

        # Use scipy skew-normal distribution for asymmetric shape
        skew = 4 if self.amplitude_mv >= 0 else -4
        shape = skewnorm.pdf(t_norm, a=skew, loc=0.5, scale=0.2)
        if shape.max() != 0:
            shape /= shape.max()

        voltage = self.amplitude_mv * shape
        return time, voltage


class LeadQRSComplex(QRSComplex):
    """QRS complex scaled for a specific lead orientation."""

    def __init__(
        self,
        lead: str,
        amplitude_scale: float = 1.0,
        polarity: float = 1.0,
        axis_deg: float = 0.0,
        **kwargs,
    ):
        base_amp = (
            kwargs.get("r_amplitude_mv", 1.0)
            * amplitude_scale
            * polarity
            * np.cos(np.radians(axis_deg))
        )
        kwargs["r_amplitude_mv"] = base_amp
        super().__init__(**kwargs)
        self.lead = lead


class LeadTWave(TWave):
    """T-wave scaled for a specific lead orientation."""

    def __init__(
        self,
        lead: str,
        amplitude_scale: float = 1.0,
        polarity: float = 1.0,
        axis_deg: float = 0.0,
        **kwargs,
    ):
        base_amp = (
            kwargs.get("amplitude_mv", 0.25)
            * amplitude_scale
            * polarity
            * np.cos(np.radians(axis_deg))
        )
        kwargs["amplitude_mv"] = base_amp
        super().__init__(**kwargs)
        self.lead = lead


class UWave(WaveformSegment):
    """U-wave segment following ventricular repolarization."""

    def __init__(self, amplitude_mv: float = 0.1, duration_ms: float = 80):
        """Initialize U-wave with clinical validation."""
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


class FibrillationWave(WaveformSegment):
    """Short oscillatory wave used for ventricular fibrillation."""

    def __init__(self, amplitude_mv: float = 1.0, duration_ms: float = 100):
        super().__init__(duration_ms, amplitude_mv)

    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate noisy sinusoid representing a fibrillatory wave."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(0, self.duration_ms / 1000.0, n_samples, endpoint=False)

        rng = np.random.default_rng()
        freq = rng.uniform(5, 10)  # Hz
        voltage = self.amplitude_mv * np.sin(2 * np.pi * freq * time)
        noise = 0.05 * self.amplitude_mv * rng.normal(size=n_samples)
        return time, voltage + noise


class LeadFibrillationWave(FibrillationWave):
    """Fibrillation wave scaled for a specific lead orientation."""

    def __init__(
        self,
        lead: str,
        amplitude_scale: float = 1.0,
        polarity: float = 1.0,
        axis_deg: float = 0.0,
        **kwargs,
    ):
        base_amp = (
            kwargs.get("amplitude_mv", 1.0)
            * amplitude_scale
            * polarity
            * np.cos(np.radians(axis_deg))
        )
        kwargs["amplitude_mv"] = base_amp
        super().__init__(**kwargs)
        self.lead = lead


class NormalSinusRhythm(ArrhythmiaPattern):
    """Normal sinus rhythm pattern."""

    def __init__(
        self,
        heart_rate_bpm: int = 70,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        """
        Initialize normal sinus rhythm.

        Parameters:
        -----------
        heart_rate_bpm : int
            Heart rate in beats per minute (60-100 normal)
        """
        super().__init__("Normal Sinus Rhythm", lead_modifiers)

        if not (50 <= heart_rate_bpm <= 120):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside reasonable range (50-120 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.rr_interval_sec = 60.0 / heart_rate_bpm

    def define_pattern(self) -> list:
        """Define normal sinus rhythm pattern."""
        pattern = []

        # Single heartbeat pattern
        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
        mod = self.lead_modifiers.get("II", {})
        qrs_complex = LeadQRSComplex(
            "II", **mod, r_amplitude_mv=1.0, duration_ms=100
        )
        t_wave = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)

        # Timing for normal sinus rhythm
        pr_interval_sec = 0.16  # 160ms PR interval
        qrs_start = pr_interval_sec  # QRS starts after PR interval

        pattern.append({"segment": p_wave, "start_time_sec": 0.0})

        pattern.append({"segment": qrs_complex, "start_time_sec": qrs_start})

        # ST segment before T-wave (approx 120ms)
        st_duration = 0.12
        t_wave_start = (
            qrs_start + qrs_complex.duration_ms / 1000.0 + st_duration
        )

        pattern.append({"segment": t_wave, "start_time_sec": t_wave_start})

        return pattern


class SinusBradycardia(ArrhythmiaPattern):
    """Sinus rhythm with a slow heart rate."""

    def __init__(
        self,
        heart_rate_bpm: int = 50,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Sinus Bradycardia", lead_modifiers)

        if not (30 <= heart_rate_bpm < 60):
            raise ValueError(
                f"Heart rate {heart_rate_bpm}bpm is outside the bradycardia range of 30-59 bpm."
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.rr_interval_sec = 60.0 / heart_rate_bpm

    def define_pattern(self) -> list:
        """Define sinus bradycardia pattern."""
        pattern = []

        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
        mod = self.lead_modifiers.get("II", {})
        qrs_complex = LeadQRSComplex("II", **mod, r_amplitude_mv=1.0, duration_ms=100)
        t_wave = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)

        pr_interval_sec = DEFAULT_PR_INTERVAL_SEC
        qrs_start = pr_interval_sec

        pattern.append({"segment": p_wave, "start_time_sec": 0.0})
        pattern.append({"segment": qrs_complex, "start_time_sec": qrs_start})

        st_duration = NORMAL_BEAT_ST_DURATION_SEC
        t_wave_start = qrs_start + qrs_complex.duration_ms / 1000.0 + st_duration

        pattern.append({"segment": t_wave, "start_time_sec": t_wave_start})

        return pattern


class SinusTachycardia(ArrhythmiaPattern):
    """Sinus rhythm with an elevated heart rate."""

    def __init__(
        self,
        heart_rate_bpm: int = 120,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Sinus Tachycardia", lead_modifiers)

        if not (heart_rate_bpm > 100 and heart_rate_bpm <= 180):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside tachycardia range (>100 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.rr_interval_sec = 60.0 / heart_rate_bpm

    def define_pattern(self) -> list:
        """Define sinus tachycardia pattern."""
        pattern = []

        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
        mod = self.lead_modifiers.get("II", {})
        qrs_complex = LeadQRSComplex("II", **mod, r_amplitude_mv=1.0, duration_ms=100)
        t_wave = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)

        pr_interval_sec = DEFAULT_PR_INTERVAL_SEC
        qrs_start = pr_interval_sec

        pattern.append({"segment": p_wave, "start_time_sec": 0.0})
        pattern.append({"segment": qrs_complex, "start_time_sec": qrs_start})

        st_duration = NORMAL_BEAT_ST_DURATION_SEC
        t_wave_start = qrs_start + qrs_complex.duration_ms / 1000.0 + st_duration

        pattern.append({"segment": t_wave, "start_time_sec": t_wave_start})

        return pattern


class AtrialFibrillation(ArrhythmiaPattern):
    """Simple atrial fibrillation pattern with irregular RR intervals."""

    def __init__(
        self,
        heart_rate_bpm: int = 90,
        duration_sec: float = 3.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Atrial Fibrillation", lead_modifiers)

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
            mod = self.lead_modifiers.get("II", {})
            qrs = LeadQRSComplex(
                "II", **mod, r_amplitude_mv=1.0, duration_ms=100
            )
            qrs_start = self._validator.snap_to_grid_time(t * 1000) / 1000.0
            pattern.append({"segment": qrs, "start_time_sec": qrs_start})

            tw_start = qrs_start + qrs.duration_ms / 1000.0 + 0.12
            t_wave = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)
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

    def __init__(
        self,
        heart_rate_bpm: int = 160,
        duration_sec: float = 3.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Ventricular Tachycardia", lead_modifiers)

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
            mod = self.lead_modifiers.get("II", {})
            qrs = LeadQRSComplex(
                "II",
                **mod,
                r_amplitude_mv=1.2,
                duration_ms=160,
                q_ratio=0.1,
                s_ratio=0.1,
            )
            qrs_start = self._validator.snap_to_grid_time(t * 1000) / 1000.0
            pattern.append({"segment": qrs, "start_time_sec": qrs_start})

            tw_start = qrs_start + qrs.duration_ms / 1000.0 + 0.08
            t_wave = LeadTWave("II", **mod, amplitude_mv=-0.2, duration_ms=160)
            tw_start = (
                self._validator.snap_to_grid_time(tw_start * 1000) / 1000.0
            )
            pattern.append({"segment": t_wave, "start_time_sec": tw_start})

            t += self.rr_interval

        return pattern


class PrematureVentricularContraction(ArrhythmiaPattern):
    """Isolated premature ventricular contraction with compensatory pause."""

    def __init__(
        self,
        heart_rate_bpm: int = 70,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Premature Ventricular Contraction", lead_modifiers)

        if not (50 <= heart_rate_bpm <= 120):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside range (50-120 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.rr_interval = 60.0 / heart_rate_bpm
        self.premature_offset = 0.3 * self.rr_interval
        self._validator = ClinicalValidator()

    def define_pattern(self) -> list:
        pattern = []

        # Example: PR_INTERVAL_SEC = 0.16 (defined elsewhere)
        pr = DEFAULT_PR_INTERVAL_SEC

        # First normal beat
        p1 = PWave(amplitude_mv=0.15, duration_ms=100)
        mod = self.lead_modifiers.get("II", {})
        qrs1 = LeadQRSComplex("II", **mod, r_amplitude_mv=1.0, duration_ms=100)
        t1 = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)

        pattern.append({"segment": p1, "start_time_sec": 0.0})
        pattern.append({"segment": qrs1, "start_time_sec": pr})
        t1_start = (
            pr + qrs1.duration_ms / 1000.0 + NORMAL_BEAT_ST_DURATION_SEC
        )  # Assuming NORMAL_BEAT_ST_DURATION_SEC = 0.12
        pattern.append({"segment": t1, "start_time_sec": t1_start})

        # PVC beat
        pvc_qrs = LeadQRSComplex(
            "II",
            **mod,
            r_amplitude_mv=1.2,
            duration_ms=160,
            q_ratio=0.1,
            s_ratio=0.1,
        )
        pvc_start = self.rr_interval - self.premature_offset
        pvc_start = (
            self._validator.snap_to_grid_time(pvc_start * 1000) / 1000.0
        )
        pattern.append({"segment": pvc_qrs, "start_time_sec": pvc_start})

        pvc_t_start = pvc_start + pvc_qrs.duration_ms / 1000.0 + 0.08
        pvc_t_start = (
            self._validator.snap_to_grid_time(pvc_t_start * 1000) / 1000.0
        )
        pvc_t = LeadTWave("II", **mod, amplitude_mv=-0.2, duration_ms=160)
        pattern.append({"segment": pvc_t, "start_time_sec": pvc_t_start})

        # Next normal beat after compensatory pause
        # Next normal beat after compensatory pause
        # P2 should occur at the next expected sinus interval if the sinus node is not reset
        p2_start_raw = 2 * self.rr_interval
        p2_start = (
            self._validator.snap_to_grid_time(p2_start_raw * 1000) / 1000.0
        )

        # QRS2 follows P2 after a normal PR interval
        next_qrs_start_raw = p2_start + pr
        next_qrs_start = (
            self._validator.snap_to_grid_time(next_qrs_start_raw * 1000)
            / 1000.0
        )

        p2 = PWave(amplitude_mv=0.15, duration_ms=100)
        qrs2 = LeadQRSComplex("II", **mod, r_amplitude_mv=1.0, duration_ms=100)
        t2 = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)

        pattern.append({"segment": p2, "start_time_sec": p2_start})
        pattern.append({"segment": qrs2, "start_time_sec": next_qrs_start})
        t2_start = next_qrs_start + qrs2.duration_ms / 1000.0 + 0.12
        t2_start = self._validator.snap_to_grid_time(t2_start * 1000) / 1000.0
        pattern.append({"segment": t2, "start_time_sec": t2_start})

        return pattern


class SecondDegreeAVBlock(ArrhythmiaPattern):
    """Simple Mobitz type II second-degree AV block."""

    def __init__(
        self,
        heart_rate_bpm: int = 75,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Second Degree AV Block", lead_modifiers)

        if not (50 <= heart_rate_bpm <= 100):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside range (50-100 bpm)"
            )

        self.rr_interval = 60.0 / heart_rate_bpm
        self._validator = ClinicalValidator()

    def define_pattern(self) -> list:
        pattern = []

        pr = 0.16

        # Beat 1 normal
        mod = self.lead_modifiers.get("II", {})
        p1 = PWave(amplitude_mv=0.15, duration_ms=100)
        qrs1 = LeadQRSComplex("II", **mod, r_amplitude_mv=1.0, duration_ms=100)
        t1 = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)
        pattern.append({"segment": p1, "start_time_sec": 0.0})
        pattern.append({"segment": qrs1, "start_time_sec": pr})
        t1_start = pr + qrs1.duration_ms / 1000.0 + 0.12
        pattern.append({"segment": t1, "start_time_sec": t1_start})

        # Beat 2 P-wave only (dropped QRS)
        p2_start = (
            self._validator.snap_to_grid_time(self.rr_interval * 1000) / 1000.0
        )
        p2 = PWave(amplitude_mv=0.15, duration_ms=100)
        pattern.append({"segment": p2, "start_time_sec": p2_start})

        # Beat 3 normal
        p3_start = (
            self._validator.snap_to_grid_time(2 * self.rr_interval * 1000)
            / 1000.0
        )
        qrs3_start = p3_start + pr
        qrs3_start = (
            self._validator.snap_to_grid_time(qrs3_start * 1000) / 1000.0
        )
        p3 = PWave(amplitude_mv=0.15, duration_ms=100)
        qrs3 = LeadQRSComplex("II", **mod, r_amplitude_mv=1.0, duration_ms=100)
        t3 = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)
        pattern.append({"segment": p3, "start_time_sec": p3_start})
        pattern.append({"segment": qrs3, "start_time_sec": qrs3_start})
        t3_start = qrs3_start + qrs3.duration_ms / 1000.0 + 0.12
        t3_start = self._validator.snap_to_grid_time(t3_start * 1000) / 1000.0
        pattern.append({"segment": t3, "start_time_sec": t3_start})

        return pattern


class AtrialFlutter(ArrhythmiaPattern):
    """Atrial flutter with 2:1 conduction pattern."""

    def __init__(
        self,
        heart_rate_bpm: int = 150,
        duration_sec: float = 3.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
    ):
        super().__init__("Atrial Flutter", lead_modifiers)

        if not (100 <= heart_rate_bpm <= 180):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside range (100-180 bpm)"
            )

        self.rr_interval = 60.0 / heart_rate_bpm
        self.flutter_interval = self.rr_interval / 2
        self.duration_sec = duration_sec
        self._validator = ClinicalValidator()

    def define_pattern(self) -> list:
        pattern = []
        t = 0.0

        while t < self.duration_sec:
            mod = self.lead_modifiers.get("II", {})
            # First flutter wave
            f1_start = self._validator.snap_to_grid_time(t * 1000) / 1000.0
            f1 = PWave(amplitude_mv=0.1, duration_ms=100)
            pattern.append({"segment": f1, "start_time_sec": f1_start})

            # Second flutter wave
            f2_start = t + self.flutter_interval
            if f2_start >= self.duration_sec:
                break
            f2_start = (
                self._validator.snap_to_grid_time(f2_start * 1000) / 1000.0
            )
            f2 = PWave(amplitude_mv=0.1, duration_ms=100)
            pattern.append({"segment": f2, "start_time_sec": f2_start})

            # Conducted QRS
            qrs_start = t + self.rr_interval
            if qrs_start >= self.duration_sec:
                break
            qrs_start = (
                self._validator.snap_to_grid_time(qrs_start * 1000) / 1000.0
            )
            qrs = LeadQRSComplex(
                "II", **mod, r_amplitude_mv=1.0, duration_ms=100
            )
            pattern.append({"segment": qrs, "start_time_sec": qrs_start})

            t_start = qrs_start + qrs.duration_ms / 1000.0 + 0.12
            t_start = (
                self._validator.snap_to_grid_time(t_start * 1000) / 1000.0
            )
            t_wave = LeadTWave("II", **mod, amplitude_mv=0.25, duration_ms=160)
            pattern.append({"segment": t_wave, "start_time_sec": t_start})

            t += self.rr_interval

        return pattern


class VentricularFibrillation(ArrhythmiaPattern):
    """Chaotic ventricular fibrillation pattern."""

    def __init__(self, duration_sec: float = 3.0, lead_modifiers: Optional[Dict[str, Dict]] = None):
        super().__init__("Ventricular Fibrillation", lead_modifiers)
        self.duration_sec = duration_sec
        self._validator = ClinicalValidator()

    def define_pattern(self) -> list:
        pattern = []
        rng = np.random.default_rng(0)
        t = 0.0
        while t < self.duration_sec:
            mod = self.lead_modifiers.get("II", {})
            amp = rng.uniform(0.5, 1.5)
            dur = rng.uniform(80, 150)
            wave = LeadFibrillationWave(
                "II",
                **mod,
                amplitude_mv=amp,
                duration_ms=self._validator.snap_to_grid_time(dur),
            )
            start = self._validator.snap_to_grid_time(t * 1000) / 1000.0
            pattern.append({"segment": wave, "start_time_sec": start})
            t += wave.duration_ms / 1000.0
        return pattern


class PulselessElectricalActivity(ArrhythmiaPattern):
    """Models the asystolic (flatline) ECG presentation seen in some PEA cases."""

    def __init__(self, duration_sec: float = 3.0, lead_modifiers: Optional[Dict[str, Dict]] = None):
        super().__init__("Pulseless Electrical Activity", lead_modifiers)
        self.duration_sec = duration_sec

    def define_pattern(self) -> list:
        # No organized electrical activity beyond baseline noise
        return []


def demo_modular_segments(output_dir=None):
    """Demonstrate modular waveform segments."""
    print("🧩 Modular Waveform Segments Demo")
    print("=" * 50)

    # Create ECG core
    ecg = ECGCore(duration_sec=3, sampling_rate=1000)

    print("Testing P-wave module...")
    p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
    ecg.add_waveform_segment(p_wave, start_time_sec=0.5)

    print("Testing QRS complex module...")
    qrs = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)
    ecg.add_waveform_segment(qrs, start_time_sec=1.2)

    print("Testing T-wave module...")
    t_wave = TWave(amplitude_mv=0.25, duration_ms=160)
    ecg.add_waveform_segment(t_wave, start_time_sec=1.4)

    print("Testing U-wave module...")
    u_wave = UWave(amplitude_mv=0.1, duration_ms=80)
    ecg.add_waveform_segment(u_wave, start_time_sec=1.65)

    # Validate grid integrity after adding segments
    ecg.validate_grid_integrity()

    # Plot result
    fig, ax = ecg.plot_with_grid()

    # Add module information
    module_info = (
        "🧩 Modular Segments Added:\\n"
        "• P-wave: 100ms, 0.15mV\\n"
        "• QRS complex: 100ms, 1.0mV\\n"
        "• T-wave: 160ms, 0.25mV\\n"
        "• U-wave: 80ms, 0.1mV\\n"
        "• Grid scaling preserved\\n"
        "• Modules are swappable"
    )

    ax.text(
        0.02,
        0.95,
        module_info,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="lightgreen", alpha=0.8),
    )

    plt.tight_layout()
    out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "."))
    out_path = out_dir / "modular_segments_demo.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Modular segments demo saved as '{out_path}'")


def demo_arrhythmia_pattern_swap():
    """Demonstrate swapping arrhythmia patterns."""
    print("\\n🔄 Arrhythmia Pattern Swap Demo")
    print("=" * 40)

    # Create ECG cores for different patterns
    ecg1 = ECGCore(duration_sec=2, sampling_rate=1000)
    ecg2 = ECGCore(duration_sec=2, sampling_rate=1000)
    ecg3 = ECGCore(duration_sec=3, sampling_rate=1000)
    ecg4 = ECGCore(duration_sec=3, sampling_rate=1000)
    ecg5 = ECGCore(duration_sec=3, sampling_rate=1000)
    ecg6 = ECGCore(duration_sec=3, sampling_rate=1000)
    ecg7 = ECGCore(duration_sec=3, sampling_rate=1000)

    # Pattern 1: Normal sinus rhythm at 70 bpm
    print("Applying Normal Sinus Rhythm (70 bpm)...")
    nsr_70 = NormalSinusRhythm(heart_rate_bpm=70)
    nsr_70.apply_to_ecg(ecg1)

    # Pattern 2: Normal sinus rhythm at 100 bpm (different pattern, same modules!)
    print("Applying Normal Sinus Rhythm (100 bpm)...")
    nsr_100 = NormalSinusRhythm(heart_rate_bpm=100)
    nsr_100.apply_to_ecg(ecg2)
    print("Applying Atrial Fibrillation...")
    af = AtrialFibrillation(heart_rate_bpm=90, duration_sec=3.0)
    af.apply_to_ecg(ecg3)

    print("Applying Ventricular Tachycardia...")
    vt = VentricularTachycardia(heart_rate_bpm=160, duration_sec=3.0)
    vt.apply_to_ecg(ecg4)

    print("Applying Premature Ventricular Contraction...")
    pvc = PrematureVentricularContraction(heart_rate_bpm=70)
    pvc.apply_to_ecg(ecg5)

    print("Applying Second Degree AV Block...")
    avb = SecondDegreeAVBlock(heart_rate_bpm=75)
    avb.apply_to_ecg(ecg6)

    print("Applying Atrial Flutter...")
    afl = AtrialFlutter(heart_rate_bpm=150, duration_sec=3.0)
    afl.apply_to_ecg(ecg7)

    # Validate both patterns
    print("\\nValidating Pattern 1 (70 bpm):")
    ecg1.validate_grid_integrity()

    print("\\nValidating Pattern 2 (100 bpm):")
    ecg2.validate_grid_integrity()
    print("\nValidating Pattern 3 (Atrial Fibrillation):")
    ecg3.validate_grid_integrity()

    print("\nValidating Pattern 4 (Ventricular Tachycardia):")
    ecg4.validate_grid_integrity()

    print("\nValidating Pattern 5 (PVC):")
    ecg5.validate_grid_integrity()

    print("\nValidating Pattern 6 (Second Degree AV Block):")
    ecg6.validate_grid_integrity()

    print("\nValidating Pattern 7 (Atrial Flutter):")
    ecg7.validate_grid_integrity()

    print("✅ Pattern swap demonstration complete!")
    print("   Same modules, different arrhythmia patterns")
    print("   Grid scaling preserved in both cases")


def demo_normal(output_dir=None):
    """Generate a normal sinus rhythm example plot."""
    ecg = ECGCore(duration_sec=3, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)
    fig, _ = ecg.plot_with_grid(show_calibration=False)
    out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "."))
    out_path = out_dir / "normal_sinus_rhythm_demo.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Normal sinus rhythm demo saved as '{out_path}'")


def demo_afib(output_dir=None):
    """Generate an atrial fibrillation example plot."""
    ecg = ECGCore(duration_sec=3, sampling_rate=1000)
    AtrialFibrillation(heart_rate_bpm=90, duration_sec=3.0).apply_to_ecg(ecg)
    fig, _ = ecg.plot_with_grid(show_calibration=False)
    out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "."))
    out_path = out_dir / "atrial_fibrillation_demo.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Atrial fibrillation demo saved as '{out_path}'")


def main():
    """Main demonstration of modular ECG architecture."""
    output_dir = Path(os.getenv("OUTPUT_DIR", "."))
    demo_modular_segments(output_dir=output_dir)
    demo_arrhythmia_pattern_swap()

    print("\\n🎯 Modular Architecture Benefits:")
    print("✅ Grid scaling never broken")
    print("✅ Waveform segments are plug-and-play")
    print("✅ Arrhythmia patterns easily swappable")
    print("✅ Clinical validation built-in")
    print("✅ Ready for complex arrhythmia development")


if __name__ == "__main__":
    main()
