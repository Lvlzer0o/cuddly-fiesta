"""Implementation of the Bundle-Branch Block arrhythmia pattern."""

from __future__ import annotations

from ..core import ECGCore
from ..segments import PWave, QRSComplex, TWave
from .normal_sinus import NormalSinusRhythm


class BundleBranchBlock(NormalSinusRhythm):
    """Represents the Bundle-Branch Block arrhythmia pattern."""

    def __init__(self, qrs_duration_ms: float = 140.0, **kwargs):
        """
        Initializes the Bundle-Branch Block pattern.

        Args:
            qrs_duration_ms: The duration of the QRS complex in milliseconds (typically > 120ms).
        """
        super().__init__(**kwargs)
        if qrs_duration_ms <= 120:
            raise ValueError("Bundle-Branch Block requires a QRS duration > 120ms.")
        self.qrs_duration_ms = qrs_duration_ms

    def _generate_cycle(self, ecg: ECGCore) -> list[tuple[PWave | QRSComplex | TWave, float]]:
        """Generates a single ECG cycle with a widened QRS complex."""
        p_wave = PWave(ecg.sampling_rate)
        
        # Create a widened QRS complex
        qrs_complex = QRSComplex(
            sampling_rate=ecg.sampling_rate,
            q_duration_ms=self.qrs_duration_ms * 0.2,  # Proportional scaling
            r_duration_ms=self.qrs_duration_ms * 0.6,
            s_duration_ms=self.qrs_duration_ms * 0.2,
        )

        t_wave = TWave(ecg.sampling_rate)

        # Timing calculations
        pr_interval_sec = self.pr_interval_ms / 1000.0
        qrs_duration_sec = qrs_complex.duration_ms / 1000.0
        st_segment_sec = 0.120  # 120ms
        t_wave_start_time = pr_interval_sec + qrs_duration_sec + st_segment_sec

        return [
            (p_wave, 0),
            (qrs_complex, pr_interval_sec),
            (t_wave, t_wave_start_time),
        ]
