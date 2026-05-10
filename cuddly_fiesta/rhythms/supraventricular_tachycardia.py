"""Implementation of the Supraventricular Tachycardia (SVT) arrhythmia pattern."""

from __future__ import annotations

from ..core import ECGCore
from ..segments import PWave, QRSComplex, TWave
from .normal_sinus import NormalSinusRhythm


class SupraventricularTachycardia(NormalSinusRhythm):
    """Represents the Supraventricular Tachycardia (SVT) arrhythmia pattern."""

    def __init__(self, heart_rate_bpm: float = 180.0, **kwargs):
        """
        Initializes the SVT pattern.

        Args:
            heart_rate_bpm: The heart rate in beats per minute (typically 150-250 bpm).
        """
        super().__init__(heart_rate_bpm=heart_rate_bpm, **kwargs)
        if not 150 <= heart_rate_bpm <= 250:
            raise ValueError("SVT typically has a heart rate between 150 and 250 bpm.")

    def _generate_cycle(self, ecg: ECGCore) -> list[tuple[PWave | QRSComplex | TWave, float]]:
        """
        Generates a single ECG cycle for SVT.

        P-waves are often difficult to see in SVT, so we'll generate them with a
        very small amplitude.
        """
        p_wave = PWave(amplitude_mv=0.05, duration_ms=80)
        qrs_complex = QRSComplex(duration_ms=80)
        t_wave = TWave(amplitude_mv=0.2, duration_ms=120)

        # Timing calculations
        pr_interval_sec = 0.12
        qrs_duration_sec = qrs_complex.duration_ms / 1000.0
        st_segment_sec = 0.080  # 80ms, can be shorter in tachycardia
        t_wave_start_time = pr_interval_sec + qrs_duration_sec + st_segment_sec

        return [
            (p_wave, 0),
            (qrs_complex, pr_interval_sec),
            (t_wave, t_wave_start_time),
        ]

    def define_pattern(self) -> None:
        """Define regular narrow-complex SVT with hidden P waves."""
        self.segments = []
        current_time = 0.0

        while current_time < self.duration_sec:
            qrs = QRSComplex(duration_ms=80)
            t_wave = TWave(amplitude_mv=0.2, duration_ms=120)

            self.add_segment(current_time, qrs)
            self.add_segment(current_time + 0.16, t_wave)

            current_time += self.rr_interval_sec
