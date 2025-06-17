"""T-wave segment for ECG waveforms."""

import numpy as np
from scipy.stats import skewnorm

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
WaveformSegment = importlib.import_module("run").WaveformSegment


class TWave(WaveformSegment):
    """T-wave segment representing ventricular repolarization.
    
    Generates a smooth, asymmetric waveform using a skewed Gaussian distribution
    to match the characteristic T-wave morphology.
    """
    
    def __init__(self, amplitude_mv: float = 0.25, duration_ms: float = 160):
        """Initialize T-wave segment.
        
        Args:
            amplitude_mv: Peak amplitude in millivolts (0.1-0.5 mV)
            duration_ms: Duration in milliseconds (120-200 ms)
            
        Raises:
            ValueError: If parameters are outside clinical ranges
        """
        if not (120 <= duration_ms <= 200):
            raise ValueError(
                f"T-wave duration {duration_ms}ms outside clinical range (120-200ms)"
            )

        if not (0.1 <= abs(amplitude_mv) <= 0.5):
            raise ValueError(
                f"T-wave amplitude {amplitude_mv}mV outside clinical range (0.1-0.5mV)"
            )

        super().__init__(duration_ms, amplitude_mv)
    
    def generate(self, sampling_rate: int) -> np.ndarray:
        """Generate T-wave using skewed Gaussian morphology.
        
        Args:
            sampling_rate: Sampling rate in Hz
            
        Returns:
            T-wave voltage values
        """
        # Time array in seconds
        t = np.linspace(0, self.duration_ms / 1000, 
                       int(self.duration_ms * sampling_rate / 1000),
                       endpoint=False)
        
        # Create skewed distribution for T-wave
        # Positive skew for positive T-waves, negative for inverted
        skew = 2.0 if self.amplitude_mv >= 0 else -2.0
        x = np.linspace(-3, 3, len(t))
        t_wave = skewnorm.pdf(x, skew) * self.amplitude_mv / 0.4  # Scale to desired amplitude
        
        # Ensure the peak is at the center
        peak_idx = np.argmax(t_wave)
        shift = len(t_wave) // 2 - peak_idx
        t_wave = np.roll(t_wave, shift)
        
        return t_wave.astype(np.float32)
