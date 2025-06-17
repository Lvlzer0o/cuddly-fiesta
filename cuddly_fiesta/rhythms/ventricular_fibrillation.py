"""Implementation of the Ventricular Fibrillation (VF) arrhythmia pattern."""

from __future__ import annotations

import numpy as np
from scipy import signal

from ..core import ArrhythmiaPattern, ECGCore


class VentricularFibrillation(ArrhythmiaPattern):
    """Represents the Ventricular Fibrillation (VF) arrhythmia pattern."""

    def __init__(self, amplitude_mv: float = 0.5, **kwargs):
        """
        Initializes the VF pattern.

        Args:
            amplitude_mv: The average amplitude of the fibrillation waves.
        """
        super().__init__(**kwargs)
        self.amplitude_mv = amplitude_mv

    def apply_to_ecg(self, ecg: ECGCore) -> None:
        """
        Applies the VF pattern to the ECG data.

        This method generates a chaotic, random signal to simulate VF.

        Args:
            ecg: The ECGCore object to modify.
        """
        # Generate white noise
        noise = np.random.randn(len(ecg.time_axis)) * self.amplitude_mv

        # Filter the noise to create a more realistic VF waveform
        # A bandpass filter can simulate the characteristic frequencies of VF (3-6 Hz)
        b, a = signal.butter(
            4, [3, 6], btype="bandpass", fs=ecg.sampling_rate
        )
        vf_signal = signal.lfilter(b, a, noise)

        ecg.voltage_data = vf_signal
