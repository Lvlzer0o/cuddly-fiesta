"""Implementation of the Torsades de Pointes arrhythmia pattern."""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import QRSComplex


class TorsadesDePointes(ArrhythmiaPattern):
    """Represents the Torsades de Pointes arrhythmia pattern."""

    def __init__(
        self,
        ventricular_rate_bpm: float = 200.0,
        twist_frequency_hz: float = 0.1,
        duration_sec: float = 10.0,
        **kwargs,
    ):
        """
        Initializes the Torsades de Pointes pattern.

        Args:
            ventricular_rate_bpm: The ventricular rate (typically 150-300 bpm).
            twist_frequency_hz: The frequency of the amplitude modulation (twisting).
        """
        super().__init__("Torsades de Pointes", **kwargs)
        self.ventricular_rate_bpm = ventricular_rate_bpm
        self.twist_frequency_hz = twist_frequency_hz
        self.duration_sec = duration_sec

    def define_pattern(self) -> None:
        """Define polymorphic wide-complex VT with rotating polarity."""
        self.segments = []
        interval_sec = 60.0 / self.ventricular_rate_bpm
        current_time = 0.0

        while current_time < self.duration_sec:
            amplitude = 1.2 * np.cos(
                2 * np.pi * self.twist_frequency_hz * current_time
            )
            qrs = QRSComplex(
                duration_ms=140,
                q_duration_ms=30,
                r_duration_ms=70,
                s_duration_ms=40,
                r_amplitude_mv=amplitude,
            )
            self.add_segment(current_time, qrs)
            current_time += interval_sec

    def apply_to_ecg(
        self, ecg: ECGCore, lead_name: Optional[str] = None
    ) -> None:
        """
        Applies the Torsades de Pointes pattern to the ECG data.

        Args:
            ecg: The ECGCore object to modify.
            lead_name: Optional target lead for the generated events.
        """
        self.duration_sec = ecg.duration_sec
        super().apply_to_ecg(ecg, lead_name=lead_name)
