"""Implementation of the Multifocal Atrial Tachycardia (MAT) arrhythmia pattern."""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import PWave, QRSComplex, TWave


class MultifocalAtrialTachycardia(ArrhythmiaPattern):
    """Represents the Multifocal Atrial Tachycardia (MAT) arrhythmia pattern."""

    def __init__(
        self,
        heart_rate_bpm: float = 120.0,
        duration_sec: float = 10.0,
        rng_seed: Optional[int] = None,
        **kwargs,
    ):
        """
        Initializes the MAT pattern.

        Args:
            heart_rate_bpm: The average heart rate in beats per minute (typically > 100).
        """
        super().__init__("Multifocal Atrial Tachycardia", **kwargs)
        if heart_rate_bpm <= 100:
            raise ValueError("MAT requires a heart rate > 100 bpm.")
        self.heart_rate_bpm = heart_rate_bpm
        self.duration_sec = duration_sec
        self._rng = np.random.default_rng(rng_seed)

    def define_pattern(self) -> None:
        """Define MAT with multiple P morphologies and variable PR intervals."""
        self.segments = []
        p_wave_morphologies = [
            {"duration_ms": 80, "amplitude_mv": 0.10},
            {"duration_ms": 90, "amplitude_mv": 0.15},
            {"duration_ms": 100, "amplitude_mv": 0.20},
        ]
        pr_intervals = [0.12, 0.16, 0.20]

        current_time_sec = 0.0
        beat_index = 0
        mean_interval = 60.0 / self.heart_rate_bpm
        while current_time_sec < self.duration_sec:
            morphology = p_wave_morphologies[
                beat_index % len(p_wave_morphologies)
            ]
            pr_interval_sec = pr_intervals[beat_index % len(pr_intervals)]

            p_wave = PWave(**morphology)
            qrs_complex = QRSComplex(duration_ms=90)
            t_wave = TWave(duration_ms=140)

            self.add_segment(current_time_sec, p_wave)
            self.add_segment(current_time_sec + pr_interval_sec, qrs_complex)
            self.add_segment(
                current_time_sec
                + pr_interval_sec
                + qrs_complex.duration_ms / 1000.0
                + 0.08,
                t_wave,
            )

            pp_variation = self._rng.uniform(-0.08, 0.08)
            current_time_sec += max(0.32, mean_interval + pp_variation)
            beat_index += 1

    def apply_to_ecg(
        self, ecg: ECGCore, lead_name: Optional[str] = None
    ) -> None:
        """
        Applies the MAT pattern to the ECG data.

        This method generates a rhythm with at least three different P-wave
        morphologies and varying PP and PR intervals.

        Args:
            ecg: The ECGCore object to modify.
            lead_name: Optional target lead for the generated events.
        """
        self.duration_sec = ecg.duration_sec
        super().apply_to_ecg(ecg, lead_name=lead_name)
