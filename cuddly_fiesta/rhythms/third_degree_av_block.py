"""Implementation of the Third-Degree (Complete) AV Block arrhythmia pattern."""

from __future__ import annotations

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import PWave, QRSComplex


class ThirdDegreeAVBlock(ArrhythmiaPattern):
    """Represents the Third-Degree (Complete) AV Block arrhythmia pattern."""

    def __init__(
        self,
        atrial_rate_bpm: float = 75.0,
        ventricular_rate_bpm: float = 40.0,
        **kwargs,
    ):
        """
        Initializes the Third-Degree AV Block pattern.

        Args:
            atrial_rate_bpm: The rate of atrial contraction (P-waves).
            ventricular_rate_bpm: The rate of ventricular contraction (QRS complexes).
        """
        super().__init__(**kwargs)
        if atrial_rate_bpm <= ventricular_rate_bpm:
            raise ValueError("Atrial rate must be greater than ventricular rate.")
        self.atrial_rate_bpm = atrial_rate_bpm
        self.ventricular_rate_bpm = ventricular_rate_bpm

    def apply_to_ecg(self, ecg: ECGCore) -> None:
        """
        Applies the Third-Degree AV Block pattern to the ECG data.

        This method generates dissociated P-waves and QRS complexes.

        Args:
            ecg: The ECGCore object to modify.
        """
        atrial_interval_sec = 60.0 / self.atrial_rate_bpm
        ventricular_interval_sec = 60.0 / self.ventricular_rate_bpm

        # Generate P-waves at the atrial rate
        for p_wave_time in np.arange(0, ecg.duration_sec, atrial_interval_sec):
            p_wave = PWave(ecg.sampling_rate)
            ecg.add_segment(p_wave, p_wave_time)

        # Generate QRS complexes at the ventricular rate
        for qrs_time in np.arange(0, ecg.duration_sec, ventricular_interval_sec):
            qrs = QRSComplex(ecg.sampling_rate)
            ecg.add_segment(qrs, qrs_time)
