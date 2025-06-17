"""Implementation of the First-Degree AV Block arrhythmia pattern."""

from __future__ import annotations

from .normal_sinus import NormalSinusRhythm


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
