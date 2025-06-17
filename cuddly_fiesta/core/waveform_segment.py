"""Base class for ECG waveform segments.

This module defines the abstract base class for all ECG waveform segments,
ensuring a consistent interface for generating and validating ECG components.
"""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

from .grid_scaling import GridScaling


class WaveformSegment(ABC):
    """Abstract base class for all ECG waveform segments.
    
    This class defines the interface that all ECG waveform segments must implement.
    Each segment represents a specific part of the ECG waveform (e.g., P wave, QRS complex).
    """
    
    def __init__(self, duration_ms: float, amplitude_mv: float):
        """Initialize a waveform segment.
        
        Args:
            duration_ms: Duration of the segment in milliseconds
            amplitude_mv: Peak amplitude of the segment in millivolts
            
        Raises:
            ValueError: If duration or amplitude don't align with ECG grid
        """
        self.duration_ms = duration_ms
        self.amplitude_mv = amplitude_mv
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate that segment parameters align with ECG grid specifications.
        
        Raises:
            ValueError: If duration or amplitude are invalid
        """
        if self.duration_ms <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration_ms} ms")
            
        if not GridScaling.validate_timing(self.duration_ms):
            # Snap to nearest grid line and warn
            snapped = GridScaling.snap_to_grid_time(self.duration_ms / 1000.0) * 1000.0
            raise ValueError(
                f"Duration {self.duration_ms} ms doesn't align with ECG grid. "
                f"Use {snapped:.1f} ms instead."
            )
            
        if not GridScaling.validate_voltage(self.amplitude_mv):
            # Snap to nearest grid line and warn
            snapped = GridScaling.snap_to_grid_voltage(self.amplitude_mv)
            raise ValueError(
                f"Amplitude {self.amplitude_mv} mV doesn't align with ECG grid. "
                f"Use {snapped:.1f} mV instead."
            )
    
    @abstractmethod
    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate the waveform segment data.
        
        Args:
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Tuple of (time, voltage) arrays representing the segment
        """
        pass
    
    def __repr__(self) -> str:
        """Return a string representation of the segment."""
        return f"{self.__class__.__name__}(duration_ms={self.duration_ms}, amplitude_mv={self.amplitude_mv})"
