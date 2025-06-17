"""U-wave segment for ECG waveforms."""

import numpy as np
from scipy.stats import norm

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
WaveformSegment = importlib.import_module("run").WaveformSegment


class UWave(WaveformSegment):
    """U-wave segment following the T-wave in some ECGs.
    
    Represents delayed repolarization of Purkinje fibers or mid-myocardial cells.
    """
    
    def __init__(self, amplitude_mv: float = 0.1, duration_ms: float = 80):
        """Initialize U-wave segment.
        
        Args:
            amplitude_mv: Peak amplitude in millivolts (0.05-0.2 mV)
            duration_ms: Duration in milliseconds (60-100 ms)
            
        Raises:
            ValueError: If parameters are outside clinical ranges
        """
        if not (60 <= duration_ms <= 100):
            raise ValueError(
                f"U-wave duration {duration_ms}ms outside clinical range (60-100ms)"
            )

        if not (0.05 <= abs(amplitude_mv) <= 0.2):
            raise ValueError(
                f"U-wave amplitude {amplitude_mv}mV outside clinical range (0.05-0.2mV)"
            )

        super().__init__(duration_ms, amplitude_mv)
    
    def generate(self, sampling_rate: int) -> np.ndarray:
        """Generate U-wave using a narrow Gaussian.
        
        Args:
            sampling_rate: Sampling rate in Hz
            
        Returns:
            U-wave voltage values
        """
        # Time array in seconds
        t = np.linspace(0, self.duration_ms / 1000, 
                       int(self.duration_ms * sampling_rate / 1000),
                       endpoint=False)
        
        # Create a simple Gaussian for the U-wave
        t_center = self.duration_ms / 2000  # Center at midpoint
        t_scaled = (t - t_center) * 1000  # Convert to ms for scaling
        
        # Narrower than T-wave, same polarity as T-wave
        u_wave = norm.pdf(t_scaled, 0, 15) * self.amplitude_mv / 0.03
        
        return u_wave.astype(np.float32)
