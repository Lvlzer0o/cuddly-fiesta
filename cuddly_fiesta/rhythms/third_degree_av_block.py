"""Implementation of the Third-Degree (Complete) AV Block arrhythmia pattern."""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import PWave, QRSComplex, TWave


class ThirdDegreeAVBlock(ArrhythmiaPattern):
    """Represents the Third-Degree (Complete) AV Block arrhythmia pattern."""

    def __init__(
        self,
        atrial_rate_bpm: float = 75.0,
        ventricular_rate_bpm: float = 40.0,
        duration_sec: float = 10.0,
        **kwargs,
    ):
        """
        Initializes the Third-Degree AV Block pattern.

        Args:
            atrial_rate_bpm: The rate of atrial contraction (P-waves).
            ventricular_rate_bpm: The rate of ventricular contraction (QRS complexes).
        """
        super().__init__("Third-Degree AV Block", **kwargs)
        if atrial_rate_bpm <= ventricular_rate_bpm:
            raise ValueError("Atrial rate must be greater than ventricular rate.")
        self.atrial_rate_bpm = atrial_rate_bpm
        self.ventricular_rate_bpm = ventricular_rate_bpm
        self.duration_sec = duration_sec

    def define_pattern(self) -> None:
        """Define independent atrial and ventricular rhythms."""
        self.segments = []
        atrial_interval_sec = 60.0 / self.atrial_rate_bpm
        ventricular_interval_sec = 60.0 / self.ventricular_rate_bpm

        for p_wave_time in np.arange(0, self.duration_sec, atrial_interval_sec):
            self.add_segment(
                float(p_wave_time),
                PWave(amplitude_mv=0.15, duration_ms=100),
            )

        for qrs_time in np.arange(0, self.duration_sec, ventricular_interval_sec):
            qrs_start = float(qrs_time)
            self.add_segment(qrs_start, QRSComplex(duration_ms=120))
            self.add_segment(qrs_start + 0.20, TWave(duration_ms=160))

    def apply_to_ecg(
        self, ecg: ECGCore, lead_name: Optional[str] = None
    ) -> None:
        """
        Applies the Third-Degree AV Block pattern to the ECG data.

        This method generates dissociated P-waves and QRS complexes.

        Args:
            ecg: The ECGCore object to modify.
            lead_name: Optional target lead for the generated events.
        """
        self.duration_sec = ecg.duration_sec
        super().apply_to_ecg(ecg, lead_name=lead_name)
