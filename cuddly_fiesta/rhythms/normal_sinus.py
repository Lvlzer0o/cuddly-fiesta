"""Normal sinus rhythm pattern."""

import numpy as np
from typing import Dict, Optional

from .base import ArrhythmiaPattern
from ..segments import PWave, QRSComplex, TWave, UWave


class NormalSinusRhythm(ArrhythmiaPattern):
    """Normal sinus rhythm with physiological variability.
    
    Generates a realistic normal sinus rhythm with:
    - Slight beat-to-beat variability in RR intervals
    - Small variations in waveform amplitudes
    - Lead-specific morphologies
    """
    
    def __init__(
        self,
        heart_rate_bpm: int = 70,
        duration_sec: float = 10.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
        rng_seed: Optional[int] = None,
    ):
        """Initialize normal sinus rhythm.
        
        Args:
            heart_rate_bpm: Heart rate in beats per minute (50-100 normal)
            duration_sec: Duration of the recording in seconds
            lead_modifiers: Optional dictionary of lead-specific modifications
            rng_seed: Optional random seed for reproducibility
        """
        super().__init__("Normal Sinus Rhythm", lead_modifiers)
        
        if not (50 <= heart_rate_bpm <= 120):
            raise ValueError(
                f"Heart rate {heart_rate_bpm} outside reasonable range (50-120 bpm)"
            )

        self.heart_rate_bpm = heart_rate_bpm
        self.duration_sec = duration_sec
        self.rr_interval_sec = 60.0 / heart_rate_bpm
        self._rng = np.random.default_rng(rng_seed)
    
    def _get_randomized_param(self, base_value: float, variation_pct: float) -> float:
        """Get a randomized parameter value within ±variation_pct of base."""
        if variation_pct <= 0:
            return base_value
        return self._rng.uniform(
            base_value * (1 - variation_pct/100),
            base_value * (1 + variation_pct/100)
        )
    
    def define_pattern(self) -> None:
        """Define the normal sinus rhythm pattern."""
        current_time = 0.0
        beat_count = 0
        
        # Generate beats until we exceed the duration
        while current_time < self.duration_sec:
            # Add slight variability to RR interval (±2%)
            rr_interval = self._get_randomized_param(self.rr_interval_sec, 2.0)
            
            # Randomize waveform parameters slightly (±5%)
            p_amp = self._get_randomized_param(0.15, 5.0)  # 0.15 mV ±5%
            qrs_amp = self._get_randomized_param(1.0, 5.0)  # 1.0 mV ±5%
            t_amp = self._get_randomized_param(0.25, 5.0)   # 0.25 mV ±5%
            
            # Create waveform segments for this beat
            p_wave = PWave(amplitude_mv=p_amp, duration_ms=100)
            qrs = QRSComplex(
                r_amplitude_mv=qrs_amp,
                duration_ms=100,
                q_ratio=0.2,
                s_ratio=0.3
            )
            t_wave = TWave(amplitude_mv=t_amp, duration_ms=160)
            
            # Add segments with proper timing
            self.add_segment(current_time, p_wave)
            self.add_segment(current_time + 0.12, qrs)  # PR interval ~120ms
            self.add_segment(current_time + 0.30, t_wave)  # ST segment ~80ms
            
            # Add U-wave occasionally (10% chance)
            if self._rng.random() < 0.1:
                u_amp = self._get_randomized_param(0.1, 10.0)  # 0.1 mV ±10%
                u_wave = UWave(amplitude_mv=u_amp, duration_ms=80)
                self.add_segment(current_time + 0.46, u_wave)  # After T-wave
            
            # Move to next beat
            current_time += rr_interval
            beat_count += 1
            
            # Add slight variability to beat timing
            if beat_count % 5 == 0:
                current_time += self._rng.uniform(-0.01, 0.01)  # ±10ms jitter
