"""Implementation of the Ventricular Fibrillation (VF) arrhythmia pattern."""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import signal

from ..core import ArrhythmiaPattern, ECGCore


class VentricularFibrillation(ArrhythmiaPattern):
    """Represents the Ventricular Fibrillation (VF) arrhythmia pattern."""

    def __init__(
        self,
        amplitude_mv: float = 0.5,
        rng_seed: Optional[int] = None,
        **kwargs,
    ):
        """
        Initializes the VF pattern.

        Args:
            amplitude_mv: The average amplitude of the fibrillation waves.
        """
        super().__init__("Ventricular Fibrillation", **kwargs)
        self.amplitude_mv = amplitude_mv
        self._rng = np.random.default_rng(rng_seed)

    def define_pattern(self) -> None:
        """VF has no discrete P/QRS/T events."""
        self.segments = []

    def apply_to_ecg(
        self, ecg: ECGCore, lead_name: Optional[str] = None
    ) -> None:
        """
        Applies the VF pattern to the ECG data.

        This method generates a chaotic, random signal to simulate VF.

        Args:
            ecg: The ECGCore object to modify.
            lead_name: Ignored; VF is generated as a signal-wide rhythm.
        """
        noise = self._rng.normal(0, 1, len(ecg.time)) * self.amplitude_mv

        # Filter the noise to create a more realistic VF waveform
        # A bandpass filter can simulate the characteristic frequencies of VF (3-6 Hz)
        b, a = signal.butter(
            4, [3, 6], btype="bandpass", fs=ecg.sampling_rate
        )
        vf_signal = signal.lfilter(b, a, noise)

        ecg.voltage = vf_signal
        if hasattr(ecg, "events"):
            ecg.events.clear()
            ecg.segments_added = ecg.events
        else:
            ecg.segments_added = []
