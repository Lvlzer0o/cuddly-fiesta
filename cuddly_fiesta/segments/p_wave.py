"""P-wave segment for ECG waveforms."""

import numpy as np
from scipy.stats import norm
# In this trimmed test version the WaveformSegment base class is defined in the
# top-level ``run.py`` module, so we load it dynamically.
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
WaveformSegment = importlib.import_module("run").WaveformSegment


class PWave(WaveformSegment):
    """P-wave segment representing atrial depolarization.
    
    Generates a smooth, asymmetric waveform using a double-Gaussian model
    to match clinical P-wave morphology.
    """
    
    def __init__(self, amplitude_mv: float = 0.15, duration_ms: float = 100):
        """Initialize P-wave segment.
        
        Args:
            amplitude_mv: Peak amplitude in millivolts (0.05-0.3 mV)
            duration_ms: Duration in milliseconds (80-120 ms)
            
        Raises:
            ValueError: If parameters are outside clinical ranges
        """
        # Validate clinical ranges
        if not (80 <= duration_ms <= 120):
            raise ValueError(
                f"P-wave duration {duration_ms}ms outside clinical range (80-120ms)"
            )

        if not (0.05 <= amplitude_mv <= 0.3):
            raise ValueError(
                f"P-wave amplitude {amplitude_mv}mV outside clinical range (0.05-0.3mV)"
            )

        super().__init__(duration_ms, amplitude_mv)
    
    def generate(self, sampling_rate: int) -> np.ndarray:
        """Generate P-wave using asymmetric double-Gaussian model.
        
        Args:
            sampling_rate: Sampling rate in Hz
            
        Returns:
            P-wave voltage values
        """
        # Time array in seconds
        t = np.linspace(0, self.duration_ms / 1000, 
                       int(self.duration_ms * sampling_rate / 1000), 
                       endpoint=False)
        
        # Center time at 40% of duration for asymmetry
        t_center = 0.4 * self.duration_ms / 1000
        t_scaled = (t - t_center) * 1000  # Convert to ms for scaling
        
        # Create asymmetric double-Gaussian
        g1 = norm.pdf(t_scaled, 0, 20)  # First peak (wider)
        g2 = norm.pdf(t_scaled, 15, 10)  # Second peak (narrower)
        
        # Combine and normalize
        p_wave = (g1 * 0.7 + g2 * 0.3) * self.amplitude_mv / max(g1.max(), g2.max())
        
        return p_wave.astype(np.float32)
