"""Implementation of the Asystole arrhythmia pattern."""

from __future__ import annotations

from typing import Optional

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore


class Asystole(ArrhythmiaPattern):
    """Represents the Asystole arrhythmia pattern (flatline)."""

    def __init__(self, **kwargs):
        """Initializes the Asystole pattern."""
        super().__init__("Asystole", **kwargs)
        # Asystole has no heart rate.
        self.heart_rate_bpm = 0

    def define_pattern(self) -> None:
        """Asystole has no waveform events."""
        self.segments = []

    def apply_to_ecg(
        self, ecg: ECGCore, lead_name: Optional[str] = None
    ) -> None:
        """
        Applies the Asystole pattern to the ECG data.

        This method generates a flatline signal, representing the absence of
        cardiac electrical activity.

        Args:
            ecg: The ECGCore object to modify.
            lead_name: Ignored; asystole is a signal-wide flatline.
        """
        ecg.voltage = np.zeros_like(ecg.time)
        if hasattr(ecg, "events"):
            ecg.events.clear()
            ecg.segments_added = ecg.events
        else:
            ecg.segments_added = []
