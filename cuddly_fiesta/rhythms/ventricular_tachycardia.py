from __future__ import annotations

from typing import List, Dict, Optional
import numpy as np

from .base import ArrhythmiaPattern
from ..segments import QRSComplex, TWave

class VentricularTachycardia(ArrhythmiaPattern):
    """Ventricular tachycardia pattern with wide QRS complexes."""

    def __init__(self, heart_rate_bpm: int = 180, duration_sec: float = 10.0) -> None:
        super().__init__("Ventricular Tachycardia")
        self.heart_rate_bpm = heart_rate_bpm
        self.duration_sec = duration_sec

    def define_pattern(self) -> None:
        """Define the pattern for ventricular tachycardia.
        
        VT has wide QRS complexes (>120ms) without discernible P waves.
        """
        # Calculate RR interval in seconds from heart rate
        rr_interval = 60.0 / self.heart_rate_bpm
        current_time = 0.0
        
        # Generate beats for the entire duration
        while current_time < self.duration_sec:
            # Wide QRS complex (140ms) with large amplitude
            qrs = QRSComplex(
                duration_ms=140,  # 140ms wide QRS
                r_amplitude_mv=2.0,  # Large amplitude
                delta_wave_duration_ms=30  # Slurred upstroke for wide QRS
            )
            
            # Inverted T wave after QRS
            t_wave = TWave(
                amplitude_mv=-0.5,  # Inverted T wave
                duration_ms=160  # Slightly longer than QRS
            )
            
            # Add QRS at current time
            self.add_segment(current_time, qrs)
            
            # Add T wave after QRS (no distinct ST segment in VT)
            self.add_segment(current_time + 0.140, t_wave)  # After QRS duration
            
            # Move to next beat
            current_time += rr_interval
    
    def apply_to_ecg(self, ecg):
        """Apply VT pattern to an ECG instance."""
        super().apply_to_ecg(ecg)
        # Add some baseline wander to make it look more realistic
        time = ecg.time
        ecg.voltage += 0.1 * np.sin(2 * np.pi * 0.2 * time)  # 0.2 Hz wander
