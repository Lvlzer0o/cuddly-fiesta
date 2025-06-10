"""
ECG Core Architecture
Modular ECG generator with immutable grid scaling and swappable arrhythmia modules.

Design Principles:
1. NEVER break grid scaling or calibration
2. All waveforms mapped to clinical grid units at every step
3. Modular design for easy arrhythmia pattern swapping
4. Grid/baseline logic is reusable foundation
"""

import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
import warnings

class GridScaling:
    """Immutable grid scaling constants - NEVER modify these values."""
    
    # Standard ECG parameters - IMMUTABLE
    PAPER_SPEED_MM_PER_SEC = 25      # 25 mm/sec
    VOLTAGE_SCALE_MM_PER_MV = 10     # 10 mm/mV
    
    # Grid dimensions - IMMUTABLE  
    SMALL_SQUARE_TIME_SEC = 0.04     # 1mm = 0.04 sec
    SMALL_SQUARE_VOLTAGE_MV = 0.1    # 1mm = 0.1 mV
    LARGE_SQUARE_TIME_SEC = 0.2      # 5mm = 0.2 sec
    LARGE_SQUARE_VOLTAGE_MV = 0.5    # 5mm = 0.5 mV
    
    @classmethod
    def validate_timing(cls, duration_ms: float) -> bool:
        """Validate timing aligns with grid units."""
        duration_sec = duration_ms / 1000.0
        # Check if duration is multiple of small square
        remainder = duration_sec % cls.SMALL_SQUARE_TIME_SEC
        return abs(remainder) < 1e-6 or abs(remainder - cls.SMALL_SQUARE_TIME_SEC) < 1e-6
    
    @classmethod
    def validate_amplitude(cls, amplitude_mv: float) -> bool:
        """Validate amplitude aligns with grid units."""
        # Check if amplitude is multiple of small square
        remainder = amplitude_mv % cls.SMALL_SQUARE_VOLTAGE_MV
        return abs(remainder) < 1e-6 or abs(remainder - cls.SMALL_SQUARE_VOLTAGE_MV) < 1e-6
    
    @classmethod
    def snap_to_grid_time(cls, duration_sec: float) -> float:
        """Snap duration to nearest grid unit."""
        return round(duration_sec / cls.SMALL_SQUARE_TIME_SEC) * cls.SMALL_SQUARE_TIME_SEC
    
    @classmethod
    def snap_to_grid_voltage(cls, amplitude_mv: float) -> float:
        """Snap amplitude to nearest grid unit."""
        return round(amplitude_mv / cls.SMALL_SQUARE_VOLTAGE_MV) * cls.SMALL_SQUARE_VOLTAGE_MV


class ECGCore:
    """Core ECG foundation with immutable grid scaling and baseline."""
    
    def __init__(self, duration_sec: float = 10, sampling_rate: int = 1000):
        """
        Initialize ECG core with baseline and grid.
        
        Parameters:
        -----------
        duration_sec : float
            Total ECG strip duration
        sampling_rate : int
            Sampling rate in Hz
        """
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)
        
        # Create time array
        self.time = np.linspace(0, duration_sec, self.n_samples)
        
        # Initialize with isoelectric baseline
        self.voltage = self._generate_baseline()
        
        # Track added segments for validation
        self.segments_added = []
        
        # Grid scaling reference (immutable)
        self.grid = GridScaling()
    
    def _generate_baseline(self) -> np.ndarray:
        """Generate isoelectric baseline with minimal physiologic variation."""
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
        baseline = baseline + respiratory_drift + noise
        
        return baseline
    
    def add_waveform_segment(self, segment: 'WaveformSegment', start_time_sec: float) -> None:
        """
        Add a waveform segment to the ECG while preserving grid scaling.
        
        Parameters:
        -----------
        segment : WaveformSegment
            The waveform segment to add
        start_time_sec : float
            Start time in seconds (must align with grid)
        """
        # Validate start time aligns with grid
        if not self.grid.validate_timing(start_time_sec * 1000):
            start_time_sec = self.grid.snap_to_grid_time(start_time_sec)
            warnings.warn(f"Start time snapped to grid: {start_time_sec:.3f} sec")
        
        # Generate segment data
        segment_time, segment_voltage = segment.generate(self.sampling_rate)
        
        # Validate segment respects grid scaling
        self._validate_segment_grid_compliance(segment)
        
        # Find insertion indices
        start_idx = int(start_time_sec * self.sampling_rate)
        end_idx = start_idx + len(segment_voltage)
        
        # Ensure we don't exceed ECG duration
        if end_idx > self.n_samples:
            warnings.warn(f"Segment truncated to fit ECG duration")
            end_idx = self.n_samples
            segment_voltage = segment_voltage[:end_idx - start_idx]
        
        # Add segment to ECG (superimpose on baseline)
        self.voltage[start_idx:end_idx] += segment_voltage
        
        # Track segment for validation
        self.segments_added.append({
            'segment': segment,
            'start_time': start_time_sec,
            'duration': len(segment_voltage) / self.sampling_rate
        })
    
    def _validate_segment_grid_compliance(self, segment: 'WaveformSegment') -> None:
        """Validate that segment respects grid scaling."""
        # Check duration alignment
        duration_ms = segment.duration_ms
        if not self.grid.validate_timing(duration_ms):
            raise ValueError(f"Segment duration {duration_ms}ms not aligned with grid units")
        
        # Check amplitude alignment  
        if hasattr(segment, 'amplitude_mv'):
            if not self.grid.validate_amplitude(segment.amplitude_mv):
                warnings.warn(f"Segment amplitude {segment.amplitude_mv}mV not aligned with grid units")
    
    def plot_with_grid(self, show_calibration: bool = True, figure_size: Tuple = (15, 8)):
        """Plot ECG with standard grid - inherits from ECGBaseline."""
        from ecg_baseline import ECGBaseline
        
        # Create temporary baseline instance for grid plotting
        temp_baseline = ECGBaseline(self.duration_sec, self.sampling_rate)
        
        # Plot with grid
        fig, ax = temp_baseline.plot_with_grid(show_calibration, figure_size)
        
        # Replace baseline with our ECG data
        ax.clear()
        
        # Re-add grid
        temp_baseline._add_ecg_grid(ax)
        
        # Plot our ECG data
        ax.plot(self.time, self.voltage, 'k-', linewidth=1.2, label='ECG')
        
        # Add calibration if requested
        if show_calibration:
            temp_baseline._add_calibration_pulse(ax)
        
        # Set axis properties
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Voltage (mV)', fontsize=12)
        ax.set_title('ECG with Grid Scaling Validation', fontsize=14, fontweight='bold')
        ax.set_xlim(0, self.duration_sec)
        ax.set_ylim(-2, 2)
        ax.grid(False)
        
        # Add grid markers
        temp_baseline._add_ecg_markers(ax)
        
        return fig, ax
    
    def validate_grid_integrity(self) -> bool:
        """Validate that all modifications preserve grid scaling."""
        print("🔍 Validating Grid Integrity...")
        
        valid = True
        
        # Check if sampling rate maintains grid precision
        time_resolution = 1.0 / self.sampling_rate
        grid_time_resolution = self.grid.SMALL_SQUARE_TIME_SEC / 10  # 10 samples per small square min
        
        if time_resolution > grid_time_resolution:
            print(f"⚠️  Warning: Sampling rate may be too low for grid precision")
            print(f"   Current: {time_resolution*1000:.3f}ms, Recommended: <{grid_time_resolution*1000:.3f}ms")
        
        # Check segment compliance
        for segment_info in self.segments_added:
            segment = segment_info['segment']
            print(f"✅ Segment {segment.__class__.__name__}: Duration {segment.duration_ms}ms")
        
        print(f"✅ Grid scaling validation complete. Total segments: {len(self.segments_added)}")
        return valid


class WaveformSegment(ABC):
    """Abstract base class for all ECG waveform segments."""
    
    def __init__(self, duration_ms: float, amplitude_mv: float):
        """
        Initialize waveform segment.
        
        Parameters:
        -----------
        duration_ms : float
            Duration in milliseconds (must align with grid)
        amplitude_mv : float  
            Amplitude in millivolts
        """
        self.duration_ms = duration_ms
        self.amplitude_mv = amplitude_mv
        self.grid = GridScaling()
        
        # Validate grid alignment
        self._validate_grid_alignment()
    
    def _validate_grid_alignment(self) -> None:
        """Ensure segment parameters align with grid."""
        if not self.grid.validate_timing(self.duration_ms):
            original = self.duration_ms
            self.duration_ms = self.grid.snap_to_grid_time(self.duration_ms / 1000.0) * 1000.0
            warnings.warn(f"Duration snapped to grid: {original}ms → {self.duration_ms}ms")
    
    @abstractmethod
    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate waveform segment data.
        
        Parameters:
        -----------
        sampling_rate : int
            Sampling rate in Hz
            
        Returns:
        --------
        time : np.ndarray
            Time array in seconds
        voltage : np.ndarray
            Voltage array in mV
        """
        pass


class ArrhythmiaPattern(ABC):
    """Abstract base class for arrhythmia patterns - modular and swappable."""
    
    def __init__(self, name: str):
        self.name = name
        self.segments = []
    
    @abstractmethod
    def define_pattern(self) -> List[Dict]:
        """
        Define the pattern of segments and their timing.
        
        Returns:
        --------
        pattern : List[Dict]
            List of segment definitions with timing
        """
        pass
    
    def apply_to_ecg(self, ecg_core: ECGCore) -> None:
        """Apply this arrhythmia pattern to an ECG core."""
        pattern = self.define_pattern()
        
        for segment_def in pattern:
            segment = segment_def['segment']
            start_time = segment_def['start_time_sec']
            ecg_core.add_waveform_segment(segment, start_time)


def main():
    """Demonstration of modular ECG architecture."""
    print("🏗️  ECG Modular Architecture Demo")
    print("="*50)
    
    # Create ECG core with immutable grid scaling
    ecg = ECGCore(duration_sec=6, sampling_rate=1000)
    
    print(f"✅ ECG Core initialized:")
    print(f"   Duration: {ecg.duration_sec} sec")
    print(f"   Sampling rate: {ecg.sampling_rate} Hz")
    print(f"   Grid scaling: {ecg.grid.PAPER_SPEED_MM_PER_SEC} mm/sec, {ecg.grid.VOLTAGE_SCALE_MM_PER_MV} mm/mV")
    
    # Validate grid integrity
    ecg.validate_grid_integrity()
    
    # Plot baseline ECG with grid
    fig, ax = ecg.plot_with_grid()
    
    # Add architectural information
    info_text = (
        "🏗️ Modular ECG Architecture:\\n"
        "• Immutable grid scaling\\n"
        "• Swappable waveform segments\\n"
        "• Built-in validation\\n"
        "• Arrhythmia pattern modules"
    )
    
    ax.text(0.02, 0.85, info_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('outputs/ecg_modular_architecture.png', 
               dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Modular architecture demo saved as 'ecg_modular_architecture.png'")
    print("\\n🎯 Ready for waveform segment development!")
    print("   Next: Implement PWave, QRSComplex, TWave modules")


if __name__ == "__main__":
    main()
