"""Implementation of the Torsades de Pointes arrhythmia pattern."""

from __future__ import annotations

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import QRSComplex


class TorsadesDePointes(ArrhythmiaPattern):
    """Represents the Torsades de Pointes arrhythmia pattern."""

    def __init__(
        self,
        ventricular_rate_bpm: float = 200.0,
        twist_frequency_hz: float = 0.1,
        **kwargs,
    ):
        """
        Initializes the Torsades de Pointes pattern.

        Args:
            ventricular_rate_bpm: The ventricular rate (typically 150-300 bpm).
            twist_frequency_hz: The frequency of the amplitude modulation (twisting).
        """
        super().__init__(**kwargs)
        self.ventricular_rate_bpm = ventricular_rate_bpm
        self.twist_frequency_hz = twist_frequency_hz

    def apply_to_ecg(self, ecg: ECGCore) -> None:
        """
        Applies the Torsades de Pointes pattern to the ECG data.

        Args:
            ecg: The ECGCore object to modify.
        """
        interval_sec = 60.0 / self.ventricular_rate_bpm
        num_beats = int(ecg.duration_sec / interval_sec)

        for i in range(num_beats):
            beat_time = i * interval_sec

            # Create a wide QRS complex, typical for ventricular rhythms
            qrs = QRSComplex(
                sampling_rate=ecg.sampling_rate,
                q_duration_ms=30,
                r_duration_ms=60,
                s_duration_ms=30,
            )

            # Modulate the amplitude with a sine wave to create the 'twisting'
            amplitude_modulation = np.sin(
                2 * np.pi * self.twist_frequency_hz * beat_time
            )
            qrs.voltage_data *= amplitude_modulation

            ecg.add_segment(qrs, beat_time)
