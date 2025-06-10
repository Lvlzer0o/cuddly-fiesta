"""
Example Waveform Segments
Demonstrates modular waveform segments that respect grid scaling.

This file shows how to create plug-and-play waveform modules that:
1. Never break grid scaling
2. Can be easily swapped for different arrhythmias
3. Validate clinical parameters
"""

import numpy as np
from ecg_core import WaveformSegment, ArrhythmiaPattern, ECGCore
from typing import Tuple
import matplotlib.pyplot as plt
import os
from pathlib import Path
from clinical_validator import ClinicalValidator
from scipy.stats import skewnorm

class PWave(WaveformSegment):
    """P-wave segment with clinical accuracy."""
    
    def __init__(self, amplitude_mv: float = 0.15, duration_ms: float = 100):
        """
        Initialize P-wave.
        
        Clinical Parameters:
        - Duration: 80-100 ms (normal atrial depolarization)  
        - Amplitude: 0.1-0.25 mV (10-25% of R wave)
        """
        # Validate clinical ranges
        if not (80 <= duration_ms <= 120):
            raise ValueError(f"P-wave duration {duration_ms}ms outside clinical range (80-120ms)")
        
        if not (0.05 <= amplitude_mv <= 0.3):
            raise ValueError(f"P-wave amplitude {amplitude_mv}mV outside clinical range (0.05-0.3mV)")
        
        super().__init__(duration_ms, amplitude_mv)
    
    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate P-wave using asymmetric double-Gaussian model."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(0, self.duration_ms / 1000.0, n_samples)
        
        # Asymmetric double-Gaussian for realistic P-wave
        # Early component: Right atrial depolarization (faster)
        # Late component: Left atrial depolarization (slower)
        
        peak_time_1 = self.duration_ms * 0.3 / 1000.0  # Right atrium peak
        peak_time_2 = self.duration_ms * 0.7 / 1000.0  # Left atrium peak
        
        sigma_1 = self.duration_ms * 0.15 / 1000.0  # Faster rise
        sigma_2 = self.duration_ms * 0.25 / 1000.0  # Slower fall
        
        # Generate components
        component_1 = 0.6 * self.amplitude_mv * np.exp(-0.5 * ((time - peak_time_1) / sigma_1) ** 2)
        component_2 = 0.4 * self.amplitude_mv * np.exp(-0.5 * ((time - peak_time_2) / sigma_2) ** 2)
        
        voltage = component_1 + component_2
        
        return time, voltage


class QRSComplex(WaveformSegment):
    """QRS complex with sharp triple-component morphology."""
    
    def __init__(self, r_amplitude_mv: float = 1.0, duration_ms: float = 100, 
                 q_ratio: float = 0.2, s_ratio: float = 0.3):
        """
        Initialize QRS complex.
        
        Clinical Parameters:
        - Duration: 80-120 ms (normal ventricular depolarization)
        - R amplitude: Reference (1.0 mV typical)
        - Q ratio: Q wave depth as fraction of R (0.1-0.3)
        - S ratio: S wave depth as fraction of R (0.2-0.4)
        """
        if not (80 <= duration_ms <= 120):
            raise ValueError(f"QRS duration {duration_ms}ms outside clinical range (80-120ms)")
        
        if not (0.5 <= r_amplitude_mv <= 3.0):
            raise ValueError(f"R amplitude {r_amplitude_mv}mV outside clinical range (0.5-3.0mV)")
        
        super().__init__(duration_ms, r_amplitude_mv)
        self.q_ratio = q_ratio
        self.s_ratio = s_ratio
    
    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate QRS using triple-component sharp model."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(0, self.duration_ms / 1000.0, n_samples)
        
        # Define component timing (sharp transitions)
        q_end = 0.3  # Q wave ends at 30% of QRS duration
        r_peak = 0.5  # R wave peaks at 50% of QRS duration  
        s_end = 1.0   # S wave ends at 100% of QRS duration
        
        voltage = np.zeros(n_samples)
        
        # Q wave (sharp downward deflection)
        q_mask = time <= (q_end * self.duration_ms / 1000.0)
        voltage[q_mask] = -self.q_ratio * self.amplitude_mv * (time[q_mask] / (q_end * self.duration_ms / 1000.0))
        
        # R wave (sharp upward peak)
        r_start = q_end * self.duration_ms / 1000.0
        r_peak_time = r_peak * self.duration_ms / 1000.0
        r_mask = (time > r_start) & (time <= r_peak_time)
        
        if np.any(r_mask):
            t_r = time[r_mask]
            # Sharp rise to peak
            voltage[r_mask] = self.amplitude_mv * (t_r - r_start) / (r_peak_time - r_start) - \
                            self.q_ratio * self.amplitude_mv
        
        # S wave (sharp downward deflection)
        s_start = r_peak_time
        s_mask = time > s_start
        
        if np.any(s_mask):
            t_s = time[s_mask]
            # Sharp fall to S depth
            s_duration = (self.duration_ms / 1000.0) - s_start
            voltage[s_mask] = self.amplitude_mv - \
                            (self.amplitude_mv + self.s_ratio * self.amplitude_mv) * \
                            (t_s - s_start) / s_duration
        
        return time, voltage


class TWave(WaveformSegment):
    """T-wave segment representing ventricular repolarization."""

    def __init__(self, amplitude_mv: float = 0.25, duration_ms: float = 160):
        """Initialize T-wave with clinical validation."""
        self._validator = ClinicalValidator()

        valid_timing, _ = self._validator.validate_timing('T_wave', duration_ms)
        valid_amp, _ = self._validator.validate_amplitude('T_wave', abs(amplitude_mv))

        if not (valid_timing and valid_amp):
            raise ValueError(
                f"T-wave parameters outside clinical range: duration={duration_ms}ms amplitude={amplitude_mv}mV"
            )

        super().__init__(duration_ms, amplitude_mv)

    def generate(self, sampling_rate: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate T-wave using skewed Gaussian morphology."""
        n_samples = int((self.duration_ms / 1000.0) * sampling_rate)
        time = np.linspace(0, self.duration_ms / 1000.0, n_samples)

        # Normalized time for morphology generation
        t_norm = np.linspace(0, 1, n_samples)

        # Use scipy skew-normal distribution for asymmetric shape
        skew = 4 if self.amplitude_mv >= 0 else -4
        shape = skewnorm.pdf(t_norm, a=skew, loc=0.5, scale=0.2)
        if shape.max() != 0:
            shape /= shape.max()

        voltage = self.amplitude_mv * shape
        return time, voltage

class NormalSinusRhythm(ArrhythmiaPattern):
    """Normal sinus rhythm pattern - modular and swappable."""
    
    def __init__(self, heart_rate_bpm: int = 70):
        """
        Initialize normal sinus rhythm.
        
        Parameters:
        -----------
        heart_rate_bpm : int
            Heart rate in beats per minute (60-100 normal)
        """
        super().__init__("Normal Sinus Rhythm")
        
        if not (50 <= heart_rate_bpm <= 120):
            raise ValueError(f"Heart rate {heart_rate_bpm} outside reasonable range (50-120 bpm)")
        
        self.heart_rate_bpm = heart_rate_bpm
        self.rr_interval_sec = 60.0 / heart_rate_bpm
    
    def define_pattern(self) -> list:
        """Define normal sinus rhythm pattern."""
        pattern = []
        
        # Single heartbeat pattern
        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
        qrs_complex = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)
        t_wave = TWave(amplitude_mv=0.25, duration_ms=160)
        
        # Timing for normal sinus rhythm
        pr_interval_sec = 0.16  # 160ms PR interval
        qrs_start = pr_interval_sec  # QRS starts after PR interval
        
        pattern.append({
            'segment': p_wave,
            'start_time_sec': 0.0
        })
        
        pattern.append({
            'segment': qrs_complex,
            'start_time_sec': qrs_start
        })

        # ST segment before T-wave (approx 120ms)
        st_duration = 0.12
        t_wave_start = qrs_start + qrs_complex.duration_ms / 1000.0 + st_duration

        pattern.append({
            'segment': t_wave,
            'start_time_sec': t_wave_start
        })

        return pattern


def demo_modular_segments(output_dir=None):
    """Demonstrate modular waveform segments."""
    print("🧩 Modular Waveform Segments Demo")
    print("="*50)
    
    # Create ECG core
    ecg = ECGCore(duration_sec=3, sampling_rate=1000)
    
    print("Testing P-wave module...")
    p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
    ecg.add_waveform_segment(p_wave, start_time_sec=0.5)
    
    print("Testing QRS complex module...")
    qrs = QRSComplex(r_amplitude_mv=1.0, duration_ms=100)
    ecg.add_waveform_segment(qrs, start_time_sec=1.2)

    print("Testing T-wave module...")
    t_wave = TWave(amplitude_mv=0.25, duration_ms=160)
    ecg.add_waveform_segment(t_wave, start_time_sec=1.4)
    
    # Validate grid integrity after adding segments
    ecg.validate_grid_integrity()
    
    # Plot result
    fig, ax = ecg.plot_with_grid()
    
    # Add module information
    module_info = (
        "🧩 Modular Segments Added:\\n"
        "• P-wave: 100ms, 0.15mV\\n"
        "• QRS complex: 100ms, 1.0mV\\n"
        "• T-wave: 160ms, 0.25mV\\n"
        "• Grid scaling preserved\\n"
        "• Modules are swappable"
    )
    
    ax.text(0.02, 0.95, module_info, transform=ax.transAxes,
           fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8))
    
    plt.tight_layout()
    out_dir = Path(output_dir or os.getenv("OUTPUT_DIR", "."))
    out_path = out_dir / 'modular_segments_demo.png'
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Modular segments demo saved as '{out_path}'")


def demo_arrhythmia_pattern_swap():
    """Demonstrate swapping arrhythmia patterns."""
    print("\\n🔄 Arrhythmia Pattern Swap Demo")
    print("="*40)
    
    # Create ECG cores for different patterns
    ecg1 = ECGCore(duration_sec=2, sampling_rate=1000)
    ecg2 = ECGCore(duration_sec=2, sampling_rate=1000)
    
    # Pattern 1: Normal sinus rhythm at 70 bpm
    print("Applying Normal Sinus Rhythm (70 bpm)...")
    nsr_70 = NormalSinusRhythm(heart_rate_bpm=70)
    nsr_70.apply_to_ecg(ecg1)
    
    # Pattern 2: Normal sinus rhythm at 100 bpm (different pattern, same modules!)
    print("Applying Normal Sinus Rhythm (100 bpm)...")
    nsr_100 = NormalSinusRhythm(heart_rate_bpm=100)
    nsr_100.apply_to_ecg(ecg2)
    
    # Validate both patterns
    print("\\nValidating Pattern 1 (70 bpm):")
    ecg1.validate_grid_integrity()
    
    print("\\nValidating Pattern 2 (100 bpm):")
    ecg2.validate_grid_integrity()
    
    print("✅ Pattern swap demonstration complete!")
    print("   Same modules, different arrhythmia patterns")
    print("   Grid scaling preserved in both cases")


def main():
    """Main demonstration of modular ECG architecture."""
    output_dir = Path(os.getenv("OUTPUT_DIR", "."))
    demo_modular_segments(output_dir=output_dir)
    demo_arrhythmia_pattern_swap()
    
    print("\\n🎯 Modular Architecture Benefits:")
    print("✅ Grid scaling never broken")
    print("✅ Waveform segments are plug-and-play")
    print("✅ Arrhythmia patterns easily swappable") 
    print("✅ Clinical validation built-in")
    print("✅ Ready for complex arrhythmia development")


if __name__ == "__main__":
    main()
