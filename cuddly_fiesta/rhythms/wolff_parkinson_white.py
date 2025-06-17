"""Implementation of the Wolff-Parkinson-White (WPW) syndrome pattern."""

from __future__ import annotations

import numpy as np

from ..core import ECGCore
from ..segments import PWave, QRSComplex, TWave
from .normal_sinus import NormalSinusRhythm


class WolffParkinsonWhite(NormalSinusRhythm):
    """Represents the Wolff-Parkinson-White (WPW) syndrome pattern."""

    def __init__(self, pr_interval_ms: float = 100.0, **kwargs):
        """
        Initializes the WPW pattern.

        Args:
            pr_interval_ms: The PR interval in milliseconds (typically < 120ms).
        """
        super().__init__(pr_interval_ms=pr_interval_ms, **kwargs)
        if pr_interval_ms >= 120:
            raise ValueError("WPW syndrome requires a PR interval < 120ms.")

    def _generate_cycle(self, ecg: ECGCore) -> list[tuple[PWave | QRSComplex | TWave, float]]:
        """
        Generates a single ECG cycle for WPW, including a delta wave.
        """
        p_wave = PWave(ecg.sampling_rate)

        # Create a QRS with a delta wave (slurred upstroke)
        delta_wave_duration_ms = 40
        qrs_complex = QRSComplex(
            sampling_rate=ecg.sampling_rate,
            q_duration_ms=20,
            r_duration_ms=60,
            s_duration_ms=40,
            delta_wave_duration_ms=delta_wave_duration_ms,
        )

        t_wave = TWave(ecg.sampling_rate)

        # Timing calculations
        pr_interval_sec = self.pr_interval_ms / 1000.0
        qrs_duration_sec = qrs_complex.duration_ms / 1000.0
        st_segment_sec = 0.100
        t_wave_start_time = pr_interval_sec + qrs_duration_sec + st_segment_sec

        return [
            (p_wave, 0),
            (qrs_complex, pr_interval_sec),
            (t_wave, t_wave_start_time),
        ]
