"""Core ECG generation engine.

This module contains the main ECGCore class which serves as the foundation
for generating and manipulating ECG signals with proper grid scaling and validation.
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt

from .grid_scaling import GridScaling
from .waveform_segment import WaveformSegment


DEFAULT_COMPONENT_AXIS_DEG = {
    "PWave": 60.0,
    "QRSComplex": 60.0,
    "TWave": 45.0,
    "UWave": 45.0,
}


class ECGCore:
    """Core ECG generation engine with grid-aligned signal processing.
    
    This class provides the foundation for generating ECG signals with proper
    grid scaling, baseline generation, and waveform segment composition.
    """
    
    def __init__(self, duration_sec: float = 10.0, sampling_rate: int = 1000):
        """Initialize the ECG core with baseline settings.
        
        Args:
            duration_sec: Total duration of the ECG signal in seconds
            sampling_rate: Sampling rate in Hz (samples per second)
            
        Raises:
            ValueError: If duration or sampling rate are invalid
        """
        if duration_sec <= 0:
            raise ValueError("Duration must be positive")
        if sampling_rate <= 0:
            raise ValueError("Sampling rate must be positive")
            
        self.duration_sec = float(duration_sec)
        self.sampling_rate = int(sampling_rate)
        self.n_samples = int(self.duration_sec * self.sampling_rate)
        
        # Create time array
        self.time = np.linspace(0, self.duration_sec, self.n_samples, endpoint=False)
        
        # Initialize with isoelectric baseline
        self.voltage = self._generate_baseline()
        
        # Track added events for validation, debugging, and multi-lead synthesis.
        self.events: List[Dict[str, object]] = []
        self.segments_added = self.events
        
        # Grid scaling reference (immutable)
        self.grid = GridScaling()
    
    def _generate_baseline(self) -> np.ndarray:
        """Generate an isoelectric baseline with minimal physiologic variation.
        
        Returns:
            A numpy array containing the baseline voltage values
        """
        # Start with true isoelectric line (0 mV)
        baseline = np.zeros(self.n_samples)
        
        # Add minimal physiologic baseline drift (respiratory influence)
        respiratory_freq = 0.25  # Hz (15 breaths/min)
        respiratory_amplitude = 0.01  # mV (very subtle)
        respiratory_drift = respiratory_amplitude * np.sin(
            2 * np.pi * respiratory_freq * self.time
        )
        
        # Add very minimal random noise (electrode interface)
        noise_amplitude = 0.005  # mV
        noise = noise_amplitude * np.random.normal(0, 1, self.n_samples)
        
        # Combine components
        return baseline + respiratory_drift + noise
    
    def add_waveform_segment(
        self, 
        segment: WaveformSegment, 
        start_time_sec: float,
        lead_name: Optional[str] = None
    ) -> None:
        """Add a waveform segment to the ECG signal.
        
        Args:
            segment: The waveform segment to add
            start_time_sec: Start time of the segment in seconds
            lead_name: Optional name of the lead for lead-specific modifications
            
        Raises:
            ValueError: If segment timing is invalid or outside signal bounds
        """
        if not 0 <= start_time_sec < self.duration_sec:
            raise ValueError(
                f"Start time {start_time_sec}s is outside signal duration {self.duration_sec}s"
            )
        
        # Generate the segment
        seg_t, seg_v = segment.generate(self.sampling_rate)
        seg_t += start_time_sec
        
        # Apply lead-specific modifications if specified
        if lead_name and hasattr(self, 'lead_modifiers') and lead_name in self.lead_modifiers:
            mod = self.lead_modifiers[lead_name]
            seg_v *= mod.get('scale', 1.0)
            seg_v += mod.get('offset', 0.0)
        
        # Find valid time indices
        valid = (seg_t < self.duration_sec) & (seg_t >= 0)
        if not np.any(valid):
            return
        
        # Find the nearest indices for the segment
        indices = np.clip(
            np.round(seg_t[valid] * self.sampling_rate).astype(int),
            0,
            len(self.time) - 1
        )
        
        # Add the segment to the output
        np.add.at(self.voltage, indices, seg_v[valid])
        
        self.events.append(
            self._build_waveform_event(segment, start_time_sec, lead_name)
        )

    def _build_waveform_event(
        self,
        segment: WaveformSegment,
        start_time_sec: float,
        lead_name: Optional[str],
    ) -> Dict[str, object]:
        component_type = segment.__class__.__name__
        duration_ms = float(getattr(segment, "duration_ms", 0.0))
        event = {
            # Backward-compatible keys used by existing tests and helpers.
            "start_time": start_time_sec,
            "segment": segment,
            "lead": lead_name,
            # Event metadata used by event-based lead synthesis.
            "component_type": component_type,
            "timing": {
                "start_sec": start_time_sec,
                "duration_sec": duration_ms / 1000.0,
                "duration_ms": duration_ms,
            },
            "shape": self._describe_segment_shape(segment),
            "axis": {
                "degrees": float(
                    getattr(
                        segment,
                        "axis_deg",
                        DEFAULT_COMPONENT_AXIS_DEG.get(component_type, 0.0),
                    )
                )
            },
            "lead_profile": {
                "profile": "standard_12_lead",
                "target_lead": lead_name,
            },
        }
        metadata = getattr(segment, "event_metadata", None)
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if (
                    key == "lead_profile"
                    and isinstance(value, dict)
                    and isinstance(event["lead_profile"], dict)
                ):
                    event["lead_profile"].update(value)
                else:
                    event[key] = value
        return event

    @staticmethod
    def _describe_segment_shape(segment: WaveformSegment) -> Dict[str, object]:
        shape: Dict[str, object] = {"class_name": segment.__class__.__name__}
        for attr in (
            "duration_ms",
            "amplitude_mv",
            "q_duration_ms",
            "r_duration_ms",
            "s_duration_ms",
            "q_amplitude_mv",
            "r_amplitude_mv",
            "s_amplitude_mv",
            "delta_wave_duration_ms",
        ):
            if hasattr(segment, attr):
                value = getattr(segment, attr)
                if isinstance(value, (int, float, np.floating)):
                    value = float(value)
                shape[attr] = value
        return shape
    
    def add_arrhythmia_pattern(
        self, 
        pattern,  # Type hint omitted to avoid circular import
        lead_name: Optional[str] = None
    ) -> None:
        """Add an arrhythmia pattern to the ECG signal.
        
        Args:
            pattern: An ArrhythmiaPattern instance
            lead_name: Optional name of the lead for lead-specific modifications
        """
        # Apply the pattern to this ECGCore instance
        pattern.apply_to_ecg(self, lead_name=lead_name)
    
    def plot(
        self, 
        show_grid: bool = True,
        title: Optional[str] = None,
        figsize: Tuple[float, float] = (15, 4),
        **plot_kwargs
    ) -> None:
        """Plot the ECG signal.
        
        Args:
            show_grid: Whether to show the ECG grid
            title: Optional plot title
            figsize: Figure size (width, height) in inches
            **plot_kwargs: Additional arguments to pass to matplotlib plot
        """
        plt.figure(figsize=figsize)
        plt.plot(self.time, self.voltage, **plot_kwargs)
        
        if title is None:
            title = "ECG Signal"
        plt.title(title)
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (mV)")
        
        if show_grid:
            self._add_ecg_grid()
        
        plt.tight_layout()
        plt.show()
    
    def _add_ecg_grid(self) -> None:
        """Add standard ECG grid to the current plot."""
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
        """Return a string representation of the ECGCore instance."""
        return (
            f"{self.__class__.__name__}("
            f"duration_sec={self.duration_sec}, "
            f"sampling_rate={self.sampling_rate}, "
            f"n_segments={len(self.segments_added)})"
        )
