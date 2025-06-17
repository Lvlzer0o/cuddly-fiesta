"""Implementation of the Asystole arrhythmia pattern."""

from __future__ import annotations

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore


class Asystole(ArrhythmiaPattern):
    """Represents the Asystole arrhythmia pattern (flatline)."""

    def __init__(self, **kwargs):
        """Initializes the Asystole pattern."""
        super().__init__(**kwargs)
        # Asystole has no heart rate.
        self.heart_rate_bpm = 0

    def apply_to_ecg(self, ecg: ECGCore) -> None:
        """
        Applies the Asystole pattern to the ECG data.

        This method generates a flatline signal, representing the absence of
        cardiac electrical activity.

        Args:
            ecg: The ECGCore object to modify.
        """
        # Generate a flatline signal
        ecg.signal = np.zeros_like(ecg.time)
        ecg.segments_added = []  # No segments in asystole
