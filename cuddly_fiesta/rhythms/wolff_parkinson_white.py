"""Implementation of the Wolff-Parkinson-White (WPW) syndrome pattern."""

from __future__ import annotations

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
        super().__init__(**kwargs)
        if pr_interval_ms >= 120:
            raise ValueError("WPW syndrome requires a PR interval < 120ms.")
        self.pr_interval_ms = pr_interval_ms

    def _generate_cycle(self, ecg: ECGCore) -> list[tuple[PWave | QRSComplex | TWave, float]]:
        """
        Generates a single ECG cycle for WPW, including a delta wave.
        """
        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)

        # Create a QRS with a delta wave (slurred upstroke)
        delta_wave_duration_ms = 40
        qrs_complex = QRSComplex(
            duration_ms=120,
            q_duration_ms=20,
            r_duration_ms=60,
            s_duration_ms=40,
            r_amplitude_mv=1.2,
            delta_wave_duration_ms=delta_wave_duration_ms,
        )

        t_wave = TWave(amplitude_mv=-0.25, duration_ms=160)

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

    def get_lead_morphology(self) -> dict:
        """Return lead-specific morphology overrides."""
        return {"V2": {"scale": 1.5}}

    def define_pattern(self) -> None:
        """Define WPW beats with short PR interval and delta-wave QRS."""
        self.segments = []
        current_time = 0.0
        pr_interval_sec = self.pr_interval_ms / 1000.0

        while current_time < self.duration_sec:
            p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
            qrs = QRSComplex(
                duration_ms=120,
                r_amplitude_mv=1.2,
                delta_wave_duration_ms=40,
            )
            t_wave = TWave(amplitude_mv=-0.25, duration_ms=160)

            self.add_segment(current_time, p_wave)
            self.add_segment(current_time + pr_interval_sec, qrs)
            self.add_segment(current_time + pr_interval_sec + 0.22, t_wave)

            current_time += self.rr_interval_sec
