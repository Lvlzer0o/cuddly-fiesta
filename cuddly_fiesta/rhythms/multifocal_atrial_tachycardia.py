"""Implementation of the Multifocal Atrial Tachycardia (MAT) arrhythmia pattern."""

from __future__ import annotations

import random

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import PWave, QRSComplex, TWave


class MultifocalAtrialTachycardia(ArrhythmiaPattern):
    """Represents the Multifocal Atrial Tachycardia (MAT) arrhythmia pattern."""

    def __init__(self, heart_rate_bpm: float = 120.0, **kwargs):
        """
        Initializes the MAT pattern.

        Args:
            heart_rate_bpm: The average heart rate in beats per minute (typically > 100).
        """
        super().__init__(**kwargs)
        if heart_rate_bpm <= 100:
            raise ValueError("MAT requires a heart rate > 100 bpm.")
        self.heart_rate_bpm = heart_rate_bpm

    def apply_to_ecg(self, ecg: ECGCore) -> None:
        """
        Applies the MAT pattern to the ECG data.

        This method generates a rhythm with at least three different P-wave
        morphologies and varying PP and PR intervals.

        Args:
            ecg: The ECGCore object to modify.
        """
        p_wave_morphologies = [
            {"p_duration_ms": 80, "p_amplitude_mv": 0.10},
            {"p_duration_ms": 90, "p_amplitude_mv": 0.15},
            {"p_duration_ms": 70, "p_amplitude_mv": 0.20},
        ]

        current_time_sec = 0.0
        while current_time_sec < ecg.duration_sec:
            # Randomly select a P-wave morphology
            morphology = random.choice(p_wave_morphologies)
            p_wave = PWave(sampling_rate=ecg.sampling_rate, **morphology)

            qrs_complex = QRSComplex(ecg.sampling_rate)
            t_wave = TWave(ecg.sampling_rate)

            # Add segments
            pr_interval_sec = np.random.uniform(0.12, 0.20)
            ecg.add_segment(p_wave, current_time_sec)
            ecg.add_segment(qrs_complex, current_time_sec + pr_interval_sec)

            st_segment_sec = 0.080
            t_wave_start_time = (
                current_time_sec
                + pr_interval_sec
                + qrs_complex.duration_ms / 1000.0
                + st_segment_sec
            )
            ecg.add_segment(t_wave, t_wave_start_time)

            # Vary the PP interval
            mean_interval = 60.0 / self.heart_rate_bpm
            pp_interval_sec = np.random.normal(mean_interval, 0.05)
            current_time_sec += pp_interval_sec
