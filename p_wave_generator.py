"""
ECG P-Wave Generator
Clinically accurate P-wave with strict grid alignment and validation.

P-WAVE SPECIFICATIONS:
- Duration: 80-100ms (target: 80ms for perfect grid alignment)
- Amplitude: 0.1-0.25 of R wave (target: 0.2mV - grid-aligned) 
- Morphology: Asymmetric double-component (right + left atrial superposition)
- Grid alignment: ENFORCED
- Isolation testing: REQUIRED before integration
"""

import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from pathlib import Path
from clinical_validator import ECGSegmentGenerator, ClinicalValidator

class PWaveGenerator(ECGSegmentGenerator):
    """Generates clinically accurate P-waves with strict validation."""
    
    def __init__(self, sampling_rate=1000, enable_noise=False, 
                 target_duration_ms=80, target_amplitude_mv=0.2):
        super().__init__(sampling_rate, enable_noise)
        
        # Ensure validator exists
        if not hasattr(self, 'validator'):
            raise RuntimeError("ClinicalValidator not properly initialized in base class")
            
        self.segment_name = 'P_wave'
        
        # Configurable clinical P-wave parameters (grid-aligned)
        self.target_duration_ms = target_duration_ms    # Default: 80ms (2 small squares)
        self.target_amplitude_mv = target_amplitude_mv  # Default: 0.2mV (2 small squares)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Validate parameters against constraints
        self._validate_parameters()
    
    def _validate_parameters(self):
        """Validate P-wave parameters against clinical constraints."""
        timing_valid, timing_msg = self.validator.validate_timing(
            self.segment_name, self.target_duration_ms)
        amplitude_valid, amplitude_msg = self.validator.validate_amplitude(
            self.segment_name, self.target_amplitude_mv)
        
        self.logger.info(f"P-Wave Parameter Validation:")
        self.logger.info(timing_msg)
        self.logger.info(amplitude_msg)
        
        if not timing_valid or not amplitude_valid:
            error_msg = f"P-wave parameters outside clinical constraints:\n{timing_msg}\n{amplitude_msg}"
            raise ValueError(error_msg)
    
    def generate_p_wave(self, start_time_ms=0):
        """
        Generate clinically accurate P-wave.
        
        Parameters:
        -----------
        start_time_ms : float
            Start time in milliseconds (will be grid-snapped)
            
        Returns:
        --------
        dict : P-wave data with time and voltage arrays
        """
        # Snap start time to grid
        snapped_start_ms = self.validator.snap_to_grid_time(start_time_ms)
        snapped_duration_ms = self.validator.snap_to_grid_time(self.target_duration_ms)
        snapped_amplitude_mv = self.validator.snap_to_grid_voltage(self.target_amplitude_mv)
        
        # Generate grid-aligned time array
        time_array, _, _ = self.validator.generate_grid_aligned_time(
            snapped_start_ms, snapped_duration_ms, self.sampling_rate)
        
        # Generate P-wave morphology
        voltage_array = self._generate_p_wave_morphology(
            time_array, snapped_start_ms/1000, snapped_duration_ms/1000, snapped_amplitude_mv)
        
        # Add optional noise
        voltage_array = self.add_physiologic_noise(voltage_array)
        
        return {
            'time': time_array,
            'voltage': voltage_array,
            'start_ms': snapped_start_ms,
            'duration_ms': snapped_duration_ms,
            'amplitude_mv': snapped_amplitude_mv,
            'segment_name': self.segment_name
        }
    
    def _raised_cosine_window(self, n, fraction=0.1):
        """
        Generate a raised cosine window for smooth onset/offset transitions.
        
        Args:
            n: Number of samples in the window
            fraction: Fraction of total duration to apply the window (0-1)
            
        Returns:
            Window array with values from 0 to 1
        """
        if n == 0:
            return np.array([])
            
        # Create raised cosine window (Hann-like but more gradual)
        t = np.linspace(-np.pi/2, np.pi/2, n)
        return 0.5 * (1 + np.sin(t))
    
    def _generate_p_wave_morphology(self, time_array, start_time_sec, duration_sec, amplitude_mv):
        """
        Generate P-wave morphology with realistic atrial depolarization pattern.
        
        Implements a physiologically accurate model with:
        - Two-component Gaussian model for right and left atrial depolarization
        - Raised cosine window for smooth onset/offset transitions
        - Precise amplitude and duration control with grid alignment
        
        Parameters:
        -----------
        time_array : ndarray
            Time points for the waveform (seconds)
        start_time_sec : float
            Start time of the P-wave (seconds)
        duration_sec : float
            Duration of the P-wave (seconds)
        amplitude_mv : float
            Peak amplitude of the P-wave (mV)
            
        Returns:
        --------
        ndarray: Generated P-wave voltage values
        """
        # Normalize time to P-wave duration (0 to 1)
        t_norm = (time_array - start_time_sec) / duration_sec
        
        # Clip to ensure we stay within [0,1] range
        t_norm = np.clip(t_norm, 0, 1)
        
        # Right atrial component (earlier, sharper)
        # Represents faster right atrial depolarization
        ra_center = 0.32  # Slightly earlier for more realistic timing
        ra_width = 0.10   # Narrower for sharper characteristics
        ra_peak_fraction = 0.42  # 42% of target amplitude
        
        right_atrial = (ra_peak_fraction * amplitude_mv * 
                       np.exp(-0.5 * ((t_norm - ra_center) / ra_width) ** 2))
        
        # Left atrial component (later, broader)
        # Represents slower left atrial depolarization
        la_center = 0.68  # Later timing
        la_width = 0.22   # Broader for gradual characteristics
        la_peak_fraction = 0.48  # 48% of target amplitude
        
        left_atrial = (la_peak_fraction * amplitude_mv * 
                      np.exp(-0.5 * ((t_norm - la_center) / la_width) ** 2))
        
        # Physiologically accurate summation of atrial components
        p_wave_raw = right_atrial + left_atrial
        
        # Scale to exact target amplitude while preserving morphology
        current_max = np.max(p_wave_raw)
        if current_max > 0:
            p_wave = p_wave_raw * (amplitude_mv / current_max)
        else:
            self.logger.warning("P-wave morphology generation resulted in zero amplitude")
            return np.zeros_like(time_array)
        
        # Apply smooth onset/offset using raised cosine window (10% of duration)
        n_samples = len(p_wave)
        window_fraction = 0.1  # 10% of duration for smooth transitions
        
        # Create onset/offset windows
        n_win = max(1, int(n_samples * window_fraction))
        onset_window = self._raised_cosine_window(n_win)
        offset_window = self._raised_cosine_window(n_win)
        
        # Apply windows if they fit within the signal
        if n_win < n_samples // 2:  # Ensure windows don't overlap
            # Apply onset window (first n_win samples)
            p_wave[:n_win] *= onset_window
            
            # Apply offset window (last n_win samples, in reverse order)
            p_wave[-n_win:] *= offset_window[::-1]
        
        return p_wave
    
    def test_isolation(self, save_plot=True, output_dir=None):
        """Test P-wave in isolation with comprehensive validation."""
        print(f"\n🔬 P-WAVE ISOLATION TEST")
        print("=" * 50)
        
        # Generate P-wave
        p_wave_data = self.generate_p_wave(start_time_ms=1000)  # Start at 1 second
        
        # Validate the generated segment
        validation_passed = self.validate_segment(
            self.segment_name, 
            p_wave_data['time'], 
            p_wave_data['voltage']
        )
        
        # Plot in isolation
        if save_plot:
            fig, ax = self.plot_segment_isolation(
                p_wave_data['time'],
                p_wave_data['voltage'],
                'P-Wave',
                'p_wave_isolation_test.png',
                output_dir=output_dir
            )
            plt.close()
        
        # Print detailed metrics
        print(f"\n📊 P-Wave Metrics:")
        print(f"  Start time: {p_wave_data['start_ms']}ms")
        print(f"  Duration: {p_wave_data['duration_ms']}ms")  
        print(f"  Amplitude: {p_wave_data['amplitude_mv']:.2f}mV")
        print(f"  Peak voltage: {np.max(p_wave_data['voltage']):.3f}mV")
        print(f"  Grid aligned: ✅")
        print(f"  Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
        
        return p_wave_data, validation_passed
    
    def generate_with_baseline(self, baseline_duration_sec=5, p_wave_start_ms=1000):
        """Generate P-wave on calibrated baseline for visual verification."""
        # Create baseline
        baseline = self.baseline_generator
        baseline.duration_sec = baseline_duration_sec
        baseline.n_samples = int(baseline_duration_sec * self.sampling_rate)
        baseline.time = np.linspace(0, baseline_duration_sec, baseline.n_samples)
        baseline.baseline = baseline._generate_baseline()
        
        # Generate P-wave
        p_wave_data = self.generate_p_wave(start_time_ms=p_wave_start_ms)
        
        # Create combined signal
        combined_time = baseline.time
        combined_voltage = baseline.baseline.copy()
        
        # Add P-wave to baseline at specified time
        start_idx = int(p_wave_start_ms / 1000 * self.sampling_rate)
        end_idx = start_idx + len(p_wave_data['voltage'])
        
        if end_idx <= len(combined_voltage):
            combined_voltage[start_idx:end_idx] += p_wave_data['voltage']
        
        return {
            'time': combined_time,
            'voltage': combined_voltage,
            'p_wave_data': p_wave_data,
            'baseline_data': baseline.get_baseline_data()
        }
    
    def plot_with_baseline(self, save_filename='p_wave_with_baseline.png', output_dir=None):
        """Plot P-wave on calibrated baseline with full ECG formatting."""
        combined_data = self.generate_with_baseline()
        
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Set background
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Plot combined signal
        ax.plot(combined_data['time'], combined_data['voltage'], 'k-', linewidth=1.5)
        
        # Add ECG grid
        self.baseline_generator._add_ecg_grid(ax)
        
        # Add calibration pulse
        self.baseline_generator._add_calibration_pulse(ax)
        
        # Add clinical markers
        self.baseline_generator._add_ecg_markers(ax)
        
        # Highlight P-wave location
        p_data = combined_data['p_wave_data']
        ax.plot(p_data['time'], p_data['voltage'], 'b-', linewidth=2.5, 
               label='P-Wave', alpha=0.8)
        
        # Set axis properties
        ax.set_xlim(0, combined_data['baseline_data']['duration_sec'])
        ax.set_ylim(-1, 2)
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Voltage (mV)', fontsize=12)
        ax.set_title('P-Wave on Calibrated ECG Baseline', fontsize=14, fontweight='bold')
        
        # Add P-wave info
        p_info = (f"P-Wave:\n"
                 f"Duration: {p_data['duration_ms']}ms\n"
                 f"Amplitude: {p_data['amplitude_mv']:.2f}mV\n"
                 f"Grid Aligned: ✅")
        
        ax.text(0.98, 0.98, p_info, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='lightblue', alpha=0.8))
        
        ax.grid(False)
        plt.tight_layout()
        
        # Save plot
        out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "."))
        out_path = out_dir / save_filename
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ P-wave with baseline saved as '{out_path}'")


def main():
    """Demonstrate P-wave generator with strict clinical validation."""
    print("🏥 ECG P-WAVE GENERATOR")
    print("="*60)
    
    # Create P-wave generator (no noise for pure testing)
    output_dir = Path(os.getenv("OUTPUT_DIR", "."))
    p_gen = PWaveGenerator(sampling_rate=1000, enable_noise=False)
    
    # Test in isolation first (REQUIRED)
    p_wave_data, validation_passed = p_gen.test_isolation(save_plot=True, output_dir=output_dir)
    
    if validation_passed:
        print("\n✅ P-wave passed isolation testing!")
        
        # Generate with baseline for visual verification
        p_gen.plot_with_baseline('p_wave_clinical_demo.png', output_dir=output_dir)
        
        print("\n🎯 P-Wave Generation Complete!")
        print("📁 Files created:")
        print("  - p_wave_isolation_test.png (isolation validation)")
        print("  - p_wave_clinical_demo.png (with baseline)")
        
    else:
        print("\n❌ P-wave FAILED isolation testing!")
        print("   Fix validation errors before proceeding.")


if __name__ == "__main__":
    main()
