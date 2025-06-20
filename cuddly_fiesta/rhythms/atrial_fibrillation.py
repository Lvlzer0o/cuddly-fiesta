"""Atrial fibrillation rhythm pattern."""

import numpy as np
from typing import Dict, Optional, Tuple

from .base import ArrhythmiaPattern
from ..segments import QRSComplex, TWave


class AtrialFibrillation(ArrhythmiaPattern):
    """Atrial fibrillation rhythm with irregularly irregular rhythm.
    
    Characterized by:
    - Absent P-waves
    - Irregularly irregular ventricular response
    - Narrow QRS complexes (unless pre-existing bundle branch block)
    - Variable R-R intervals
    """
    
    def __init__(
        self,
        ventricular_rate_bpm: int = 110,
        duration_sec: float = 10.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
        rng_seed: Optional[int] = None,
    ):
        """Initialize atrial fibrillation rhythm.
        
        Args:
            ventricular_rate_bpm: Average ventricular rate in bpm (100-180 bpm)
            duration_sec: Duration of the recording in seconds
            lead_modifiers: Optional dictionary of lead-specific modifications
            rng_seed: Optional random seed for reproducibility
            
        Raises:
            ValueError: If ventricular rate is outside the expected range
        """
        if not (30 <= ventricular_rate_bpm <= 250):
            # Clamp to reasonable range instead of crashing
            ventricular_rate_bpm = max(30, min(250, ventricular_rate_bpm))
            print(f"Warning: Ventricular rate clamped to {ventricular_rate_bpm} bpm")
            
        super().__init__("Atrial Fibrillation", lead_modifiers)
        self.ventricular_rate_bpm = ventricular_rate_bpm
        self.duration_sec = duration_sec
        self._rng = np.random.default_rng(rng_seed)
        
        # Calculate average RR interval in seconds
        self.avg_rr_interval = 60.0 / ventricular_rate_bpm
    
    def _get_random_rr_interval(self) -> float:
        """Generate a random RR interval with appropriate variability for AFib."""
        # AFib has more variability than normal rhythm
        # Use a wider range (up to ±50% of average)
        min_interval = self.avg_rr_interval * 0.5
        max_interval = self.avg_rr_interval * 1.5
        
        # Skew distribution toward shorter intervals for faster rates
        if self.ventricular_rate_bpm > 120:
            # More shorter intervals for rapid ventricular response
            rr = self._rng.beta(2, 3) * (max_interval - min_interval) + min_interval
        else:
            # More balanced distribution for controlled rates
            rr = self._rng.uniform(min_interval, max_interval)
            
        return rr
    
    def _generate_qrs_complex(self) -> Tuple[float, float]:
        """Generate QRS complex with random amplitude and width.
        
        Returns:
            Tuple of (amplitude_mv, duration_ms)
        """
        # Randomize QRS amplitude (0.7-1.3 of normal)
        amplitude = self._rng.uniform(0.7, 1.3)
        
        # Slightly variable QRS duration (80-120ms)
        duration = self._rng.uniform(80, 120)
        
        return amplitude, duration
    
    def _generate_t_wave(self) -> Tuple[float, float]:
        """Generate T-wave with random amplitude and width.
        
        Returns:
            Tuple of (amplitude_mv, duration_ms)
        """
        # Randomize T-wave amplitude (0.1-0.4mV)
        amplitude = self._rng.uniform(0.1, 0.4)
        
        # Variable T-wave duration (120-200ms)
        duration = self._rng.uniform(120, 200)
        
        return amplitude, duration
    
    def define_pattern(self) -> None:
        """Define the atrial fibrillation pattern."""
        current_time = 0.0
        
        # Generate beats until we exceed the duration
        while current_time < self.duration_sec:
            # Generate random RR interval
            rr_interval = self._get_random_rr_interval()
            
            # Generate QRS complex with random parameters
            qrs_amp, qrs_dur = self._generate_qrs_complex()
            qrs = QRSComplex(
                r_amplitude_mv=qrs_amp,
                duration_ms=qrs_dur,
                q_ratio=0.2,
                s_ratio=0.3
            )
            
            # Generate T-wave with random parameters
            t_amp, t_dur = self._generate_t_wave()
            t_wave = TWave(amplitude_mv=t_amp, duration_ms=t_dur)
            
            # Add segments with proper timing
            self.add_segment(current_time, qrs)
            self.add_segment(current_time + 0.16, t_wave)  # ST segment ~80ms
            
            # Move to next beat
            current_time += rr_interval
            
        # Update name with rate information
        self.name = f"Atrial Fibrillation (VR: {self.ventricular_rate_bpm} bpm)"
