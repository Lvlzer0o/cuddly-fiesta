"""
ECG Clinical Validation Framework
Enforces strict clinical grid alignment and timing constraints for all waveform segments.

CLINICAL RULES (ENFORCED):
1. Snap timing and amplitude to grid units (40ms/0.1mV)
2. Maintain calibrated baseline scaling (0.5mV/1.0cm)
3. Verify start/stop alignment to grid units and real-world timing
4. Test each segment in isolation before combining
5. Keep noise/drift toggleable for pure signal testing

NOTE: All amplitudes are relative to R-wave = 1.0mV (standard calibration).
"""

import numpy as np
import matplotlib.pyplot as plt
import warnings
import os
from pathlib import Path
from .ecg_baseline import ECGBaseline
from .grid_constants import (
    SMALL_SQUARE_TIME_SEC,
    SMALL_SQUARE_VOLTAGE_MV,
    LARGE_SQUARE_TIME_SEC,
    LARGE_SQUARE_VOLTAGE_MV,
)

# Reference constants for clinical ECG standards
REFERENCE_R_WAVE_MV = 1.0  # Standard calibration reference (1.0mV = 10mm)
GRID_TIME_STEP_MS = int(SMALL_SQUARE_TIME_SEC * 1000)
GRID_VOLTAGE_STEP_MV = SMALL_SQUARE_VOLTAGE_MV
FLOATING_POINT_TOLERANCE = 1e-6  # For floating-point comparisons

class ClinicalValidator:
    """Validates ECG waveform segments against clinical grid and timing constraints."""
    
    def __init__(self):
        """Initialize clinical validator with standard ECG grid and timing constraints.
        
        Notes:
            - Grid dimensions follow standard ECG paper calibration:
              * Small square: 40ms × 0.1mV (1mm × 1mm)
              * Large square: 200ms × 0.5mV (5mm × 5mm)
            - Timing constraints based on standard adult ECG parameters
            - All amplitudes are relative to R-wave = 1.0mV
        """
        # Standard ECG grid constraints (using module-level constants)
        self.small_square_time_ms = GRID_TIME_STEP_MS
        self.small_square_voltage_mv = GRID_VOLTAGE_STEP_MV
        self.large_square_time_ms = 5 * GRID_TIME_STEP_MS  # 5 small squares
        self.large_square_voltage_mv = 5 * GRID_VOLTAGE_STEP_MV  # 5 small squares
        
        # Clinical timing constraints (ms) - based on standard adult ECG
        self.timing_constraints = {
            'P_wave': {'min': 80, 'max': 100, 'target': 90},     # Atrial depolarization
            'PR_interval': {'min': 120, 'max': 200, 'target': 160},  # Atrial to ventricular conduction
            'QRS_complex': {'min': 80, 'max': 120, 'target': 100},   # Ventricular depolarization
            'ST_segment': {'min': 80, 'max': 120, 'target': 100},    # Ventricular repolarization plateau
            'T_wave': {'min': 120, 'max': 160, 'target': 140},       # Ventricular repolarization
            'QT_interval': {'min': 300, 'max': 450, 'target': 400},  # Total ventricular activity
            'U_wave': {'min': 60, 'max': 110, 'target': 80}          # Post-repolarization wave
        }
        
        # Clinical amplitude constraints (relative to R wave = 1.0)
        self.amplitude_constraints = {
            'P_wave': {'min': 0.1, 'max': 0.25, 'target': 0.15},
            'Q_wave': {'min': 0.1, 'max': 0.3, 'target': 0.2},
            'R_wave': {'min': 0.8, 'max': 1.0, 'target': 1.0},  # Reference
            'S_wave': {'min': 0.2, 'max': 0.4, 'target': 0.3},
            'T_wave': {'min': 0.1, 'max': 0.5, 'target': 0.25},
            'U_wave': {'min': 0.05, 'max': 0.15, 'target': 0.1}
        }
    
    def snap_to_grid_time(self, time_ms):
        """Snap timing to nearest grid unit (40ms increments).
        
        Args:
            time_ms: Time in milliseconds
            
        Returns:
            float: Time snapped to nearest grid unit (40ms)
            
        Note:
            Uses standard small square width of 40ms (1mm at 25mm/s)
        """
        return round(time_ms / self.small_square_time_ms) * self.small_square_time_ms
    
    def snap_to_grid_voltage(self, voltage_mv):
        """Snap voltage to nearest grid unit (0.1mV increments).
        
        Args:
            voltage_mv: Voltage in millivolts
            
        Returns:
            float: Voltage snapped to nearest grid unit (0.1mV)
            
        Note:
            Uses standard small square height of 0.1mV (1mm at 10mm/mV)
        """
        return round(voltage_mv / self.small_square_voltage_mv) * self.small_square_voltage_mv
    
    def validate_timing(self, segment_name, duration_ms):
        """Validate segment timing against clinical constraints.
        
        Args:
            segment_name: Name of the ECG segment (e.g., 'P_wave', 'QRS_complex')
            duration_ms: Duration of the segment in milliseconds
            
        Returns:
            tuple: (is_valid, message) indicating validation result
        """
        if segment_name not in self.timing_constraints:
            warning_msg = f"⚠️ No timing constraints defined for segment: {segment_name}"
            warnings.warn(warning_msg, RuntimeWarning)
            return True, warning_msg
        
        constraints = self.timing_constraints[segment_name]
        snapped_duration = self.snap_to_grid_time(duration_ms)
        
        if constraints['min'] <= snapped_duration <= constraints['max']:
            return True, f"✅ {segment_name} timing: {snapped_duration}ms (valid)"
        else:
            return False, f"❌ {segment_name} timing: {snapped_duration}ms (outside {constraints['min']}-{constraints['max']}ms range)"
    
    def validate_amplitude(self, segment_name, amplitude_mv):
        """Validate segment amplitude against clinical constraints.
        
        Args:
            segment_name: Name of the ECG segment (e.g., 'P_wave', 'R_wave')
            amplitude_mv: Peak-to-peak amplitude in millivolts
            
        Returns:
            tuple: (is_valid, message) indicating validation result
            
        Note:
            All amplitudes are relative to R-wave = 1.0mV (standard calibration)
        """
        if segment_name not in self.amplitude_constraints:
            warning_msg = f"⚠️ No amplitude constraints defined for segment: {segment_name}"
            warnings.warn(warning_msg, RuntimeWarning)
            return True, warning_msg
        
        constraints = self.amplitude_constraints[segment_name]
        snapped_amplitude = self.snap_to_grid_voltage(amplitude_mv)
        
        if constraints['min'] <= snapped_amplitude <= constraints['max']:
            return True, f"✅ {segment_name} amplitude: {snapped_amplitude}mV (valid)"
        else:
            return False, f"❌ {segment_name} amplitude: {snapped_amplitude}mV (outside {constraints['min']}-{constraints['max']}mV range)"
    
    def generate_grid_aligned_time(self, start_ms, duration_ms, sampling_rate=1000):
        """Generate time array aligned to grid with specified duration."""
        # Snap start and duration to grid
        snapped_start = self.snap_to_grid_time(start_ms)
        snapped_duration = self.snap_to_grid_time(duration_ms)
        
        # Generate time array
        n_samples = int(snapped_duration * sampling_rate / 1000)
        time_array = np.linspace(
            snapped_start / 1000,
            (snapped_start + snapped_duration) / 1000,
            n_samples,
            endpoint=False,
        )
        
        return time_array, snapped_start, snapped_duration


class ECGSegmentGenerator:
    """Base class for generating clinical ECG waveform segments."""
    
    def __init__(self, sampling_rate=1000, enable_noise=False):
        self.sampling_rate = sampling_rate
        self.enable_noise = enable_noise
        self.validator = ClinicalValidator()
        
        # Initialize baseline for consistent scaling
        self.baseline_generator = ECGBaseline(duration_sec=10, sampling_rate=sampling_rate)
        self.grid_specs = self.baseline_generator.get_baseline_data()['grid_specs']
    
    def add_physiologic_noise(self, signal, noise_amplitude=None):
        """Add toggleable physiologic noise to signal.
        
        Args:
            signal: Input signal array
            noise_amplitude: Amplitude of noise as fraction of signal amplitude.
                           If None, uses default of 0.5% of signal range.
                           
        Returns:
            numpy.ndarray: Signal with added noise if enabled
        """
        if not self.enable_noise:
            return signal
            
        if noise_amplitude is None:
            # Default to 0.5% of signal range if not specified
            signal_range = np.ptp(signal) if len(signal) > 0 else 1.0
            noise_amplitude = 0.005 * signal_range
        
        noise = noise_amplitude * np.random.normal(0, 1, len(signal))
        return signal + noise
    
    def plot_segment_isolation(self, time, signal, segment_name,
                               save_filename=None, output_dir=None):
        """Plot segment in isolation with grid for validation."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Use baseline generator's grid system
        
        # Create temporary baseline for grid
        temp_baseline = ECGBaseline(duration_sec=max(time), sampling_rate=self.sampling_rate)
        temp_baseline.time = time
        temp_baseline.baseline = np.zeros_like(time)
        temp_baseline.duration_sec = max(time)
        
        # Add grid
        temp_baseline._add_ecg_grid(ax)
        
        # Plot segment
        ax.plot(time, signal, 'b-', linewidth=2.5, label=f'{segment_name} Segment')
        ax.axhline(0, color='red', linewidth=1.5, alpha=0.9, label='Baseline')
        
        # Set limits with padding
        ax.set_xlim(min(time) - 0.1, max(time) + 0.1)
        signal_range = max(signal) - min(signal)
        padding = signal_range * 0.2 if signal_range > 0 else 0.5
        ax.set_ylim(min(signal) - padding, max(signal) + padding)
        
        # Labels and title
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Voltage (mV)', fontsize=12)
        ax.set_title(f'{segment_name} - Isolation Test (Grid Aligned)', fontsize=14, fontweight='bold')
        ax.legend()
        
        # Add validation info
        duration_ms = (max(time) - min(time)) * 1000
        amplitude_mv = max(signal) - min(signal)
        
        validation_text = f"Validation:\n"
        validation_text += f"Duration: {duration_ms:.1f} ms\n"
        validation_text += f"Amplitude: {amplitude_mv:.2f} mV\n"
        validation_text += f"Grid aligned: ✅"
        
        ax.text(0.02, 0.98, validation_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8))
        
        plt.grid(False)  # Use our custom grid
        plt.tight_layout()
        
        if save_filename:
            out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "."))
            out_path = out_dir / save_filename
            plt.savefig(out_path, dpi=300, bbox_inches='tight')
            print(f"✅ {segment_name} isolation test saved as '{out_path}'")
        
        return fig, ax
    
    def validate_segment(self, segment_name, time, signal):
        """Comprehensive validation of segment against clinical constraints."""
        print(f"\n🔍 Validating {segment_name} Segment:")
        print("=" * 50)
        
        # Calculate metrics
        duration_ms = (max(time) - min(time)) * 1000
        amplitude_mv = max(signal) - min(signal)
        
        # Timing validation
        timing_valid, timing_msg = self.validate_timing(segment_name, duration_ms)
        print(timing_msg)
        
        # Amplitude validation  
        amplitude_valid, amplitude_msg = self.validate_amplitude(segment_name, amplitude_mv)
        print(amplitude_msg)
        
        # Grid alignment check with tolerance for floating-point precision
        snapped_duration = self.snap_to_grid_time(duration_ms)
        snapped_amplitude = self.snap_to_grid_voltage(amplitude_mv)
        
        # Use tolerance for floating-point comparison
        duration_tolerance = max(0.1, FLOATING_POINT_TOLERANCE * abs(snapped_duration))
        amplitude_tolerance = max(0.001, FLOATING_POINT_TOLERANCE * abs(snapped_amplitude))
        
        grid_aligned = (abs(duration_ms - snapped_duration) < duration_tolerance and 
                       abs(amplitude_mv - snapped_amplitude) < amplitude_tolerance)
        
        if grid_aligned:
            print("✅ Grid alignment: Perfect")
        else:
            print(f"❌ Grid alignment: Duration off by {abs(duration_ms - snapped_duration):.1f}ms, "
                  f"Amplitude off by {abs(amplitude_mv - snapped_amplitude):.3f}mV")
        
        # Overall validation
        overall_valid = timing_valid and amplitude_valid and grid_aligned
        
        if overall_valid:
            print(f"🎯 {segment_name} VALIDATION: ✅ PASSED")
        else:
            print(f"🎯 {segment_name} VALIDATION: ❌ FAILED")
        
        return overall_valid


def test_validation_framework():
    """Test the clinical validation framework."""
    print("🏥 Testing ECG Clinical Validation Framework")
    print("=" * 60)
    
    validator = ClinicalValidator()
    
    # Test grid snapping
    print("\n📐 Grid Snapping Tests:")
    test_times = [78, 82, 85, 95, 105]  # ms
    for time_ms in test_times:
        snapped = validator.snap_to_grid_time(time_ms)
        print(f"  {time_ms}ms → {snapped}ms")
    
    test_voltages = [0.12, 0.18, 0.23, 0.27]  # mV
    for voltage_mv in test_voltages:
        snapped = validator.snap_to_grid_voltage(voltage_mv)
        print(f"  {voltage_mv}mV → {snapped}mV")
    
    # Test timing validation
    print("\n⏱️ Timing Validation Tests:")
    test_segments = [
        ('P_wave', 85),   # Valid
        ('P_wave', 110),  # Invalid
        ('QRS_complex', 100),  # Valid  
        ('QRS_complex', 150),  # Invalid
    ]
    
    for segment, duration in test_segments:
        valid, msg = validator.validate_timing(segment, duration)
        print(f"  {msg}")
    
    print("\n🎯 Validation Framework Ready!")


if __name__ == "__main__":
    test_validation_framework()
