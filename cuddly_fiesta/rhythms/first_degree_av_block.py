"""Implementation of the First-Degree AV Block arrhythmia pattern."""

from __future__ import annotations

from .normal_sinus import NormalSinusRhythm
from ..segments import PWave, QRSComplex, TWave


class FirstDegreeAVBlock(NormalSinusRhythm):
    """Represents the First-Degree AV Block arrhythmia pattern."""

    def __init__(self, pr_interval_ms: float = 240.0, **kwargs):
        """
        Initializes the First-Degree AV Block pattern.

        Args:
            pr_interval_ms: The PR interval in milliseconds (typically > 200ms).
        """
        super().__init__(**kwargs)
        if pr_interval_ms <= 200:
            raise ValueError("First-Degree AV Block requires a PR interval > 200ms.")
        self.pr_interval_ms = pr_interval_ms

    def define_pattern(self) -> None:
        """Define sinus beats with a prolonged PR interval."""
        self.segments = []
        current_time = 0.0
        pr_interval_sec = self.pr_interval_ms / 1000.0

        while current_time < self.duration_sec:
            p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
            qrs = QRSComplex(duration_ms=100)
            t_wave = TWave(amplitude_mv=0.25, duration_ms=160)

            self.add_segment(current_time, p_wave)
            self.add_segment(current_time + pr_interval_sec, qrs)
            self.add_segment(current_time + pr_interval_sec + 0.18, t_wave)

            current_time += self.rr_interval_sec
