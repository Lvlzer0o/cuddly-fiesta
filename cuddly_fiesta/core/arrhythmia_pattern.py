"""Base class for ECG arrhythmia patterns.

This module defines the abstract base class for all ECG arrhythmia patterns,
ensuring a consistent interface for generating and applying different cardiac rhythms.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

from .waveform_segment import WaveformSegment
from .grid_scaling import GridScaling


class ArrhythmiaPattern(ABC):
    """Abstract base class for ECG arrhythmia patterns.
    
    This class defines the interface that all ECG arrhythmia patterns must implement.
    Each pattern represents a specific cardiac rhythm (e.g., normal sinus rhythm, 
    atrial fibrillation).
    """
    
    def __init__(
        self, 
        name: str, 
        lead_modifiers: Optional[Dict[str, Dict]] = None
    ) -> None:
        """Initialize an arrhythmia pattern.
        
        Args:
            name: Human-readable name of the arrhythmia pattern
            lead_modifiers: Optional dictionary of lead-specific modifications
        """
        self.name = name
        self.segments: List[Tuple[float, WaveformSegment]] = []
        self.lead_modifiers = lead_modifiers or {}
    
    def add_segment(
        self,
        time_sec: float,
        segment: WaveformSegment,
        lead_name: Optional[str] = None
    ) -> None:
        """Add a waveform segment to the pattern.
        
        Args:
            time_sec: Start time of the segment in seconds
            segment: WaveformSegment instance to add
            lead_name: Optional lead name if segment is lead-specific
        """
        snapped = GridScaling.snap_to_grid_time(time_sec)
        self.segments.append((snapped, segment, lead_name))

    def apply_to_ecg(self, ecg, lead_name: Optional[str] = None) -> None:
        """Apply this pattern's segments to an ``ECGCore`` instance."""
        self.define_pattern()
        for start, segment, lead in self.segments:
            if 0 <= start < ecg.duration_sec:
                ecg.add_waveform_segment(segment, start, lead_name or lead)
    
    @abstractmethod
    def define_pattern(self) -> None:
        """Define the pattern of segments and their timing.
        
        Subclasses must implement this method to define the specific
        waveform segments that make up the arrhythmia pattern.
        """
        pass
    
    def generate(
        self, 
        duration_sec: float, 
        sampling_rate: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate the complete ECG signal for this pattern.
        
        Args:
            duration_sec: Total duration of the signal in seconds
            sampling_rate: Sampling rate in Hz
            
        Returns:
            Tuple of (time, voltage) arrays representing the ECG signal
        """
        # Create time array
        n_samples = int(duration_sec * sampling_rate)
        time = np.linspace(0, duration_sec, n_samples, endpoint=False)
        voltage = np.zeros_like(time)
        
        # Generate each segment and add to the signal
        for seg_time, segment, lead_name in self.segments:
            if seg_time >= duration_sec:
                continue
                
            # Generate the segment
            seg_t, seg_v = segment.generate(sampling_rate)
            seg_t += seg_time
            
            # Apply lead-specific modifications if specified
            if lead_name and lead_name in self.lead_modifiers:
                mod = self.lead_modifiers[lead_name]
                seg_v *= mod.get('scale', 1.0)
                seg_v += mod.get('offset', 0.0)
            
            # Add to the output signal
            valid = (seg_t < duration_sec) & (seg_t >= 0)
            if not np.any(valid):
                continue
                
            # Find the nearest indices for the segment
            indices = np.clip(
                np.round(seg_t[valid] * sampling_rate).astype(int),
                0,
                len(time) - 1
            )
            
            # Add the segment to the output
            np.add.at(voltage, indices, seg_v[valid])
        
        return time, voltage
    
    def plot(
        self, 
        duration_sec: float = 10.0, 
        sampling_rate: int = 1000,
        show_grid: bool = True,
        **plot_kwargs
    ) -> None:
        """Plot the arrhythmia pattern.
        
        Args:
            duration_sec: Duration to plot in seconds
            sampling_rate: Sampling rate in Hz
            show_grid: Whether to show the ECG grid
            **plot_kwargs: Additional arguments to pass to matplotlib plot
        """
        import matplotlib.pyplot as plt
        
        # Generate the signal
        time, voltage = self.generate(duration_sec, sampling_rate)
        
        # Create the plot
        plt.figure(figsize=plot_kwargs.pop('figsize', (15, 4)))
        plt.plot(time, voltage, **plot_kwargs)
        plt.title(f"{self.name} Pattern")
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (mV)")
        
        if show_grid:
            self._add_ecg_grid()
        
        plt.tight_layout()
        plt.show()
    
    def _add_ecg_grid(self) -> None:
        """Add standard ECG grid to the current plot."""
        import matplotlib.pyplot as plt
        
        # Get current axis limits
        xlim = plt.xlim()
        ylim = plt.ylim()
        
        # Add major (5mm) and minor (1mm) grid lines
        for x in np.arange(0, xlim[1], 0.2):  # 0.2s = 5mm at 25mm/s
            plt.axvline(x, color='red', alpha=0.2, linestyle='-', zorder=0)
            
        for x in np.arange(0, xlim[1], 0.04):  # 0.04s = 1mm at 25mm/s
            plt.axvline(x, color='gray', alpha=0.1, linestyle=':', zorder=0)
            
        for y in np.arange(
            np.floor(ylim[0] * 10) / 10, 
            np.ceil(ylim[1] * 10) / 10 + 0.1, 
            0.1  # 0.1mV = 1mm at 10mm/mV
        ):
            plt.axhline(y, color='gray', alpha=0.1, linestyle=':', zorder=0)
        
        # Reset limits
        plt.xlim(xlim)
        plt.ylim(ylim)
    
    def __repr__(self) -> str:
        """Return a string representation of the pattern."""
        return f"{self.__class__.__name__}(name='{self.name}')"
