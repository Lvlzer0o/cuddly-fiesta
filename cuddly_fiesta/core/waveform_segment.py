"""Base class for ECG waveform segments.

This module defines the abstract base class for all ECG waveform segments,
ensuring a consistent interface for generating and validating ECG components.
"""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np

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
            ValueError: If duration is invalid
        """
        self.duration_ms = duration_ms
        self.amplitude_mv = amplitude_mv
        self._validate_parameters()
    
    def _validate_parameters(self) -> None:
        """Validate basic segment parameters.
        
        Raises:
            ValueError: If duration is invalid
        """
        if self.duration_ms <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration_ms} ms")
    
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
