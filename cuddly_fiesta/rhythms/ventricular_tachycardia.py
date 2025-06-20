from __future__ import annotations

from typing import List, Dict, Optional
import numpy as np

from .base import ArrhythmiaPattern
from ..segments import QRSComplex, TWave

class VentricularTachycardia(ArrhythmiaPattern):
    """Ventricular tachycardia pattern with wide QRS complexes."""

    def __init__(self, heart_rate_bpm: int = 180) -> None:
        super().__init__("Ventricular Tachycardia")
        self.heart_rate_bpm = heart_rate_bpm

    def define_pattern(self) -> List[Dict]:
        """Define the pattern for ventricular tachycardia.
        
        Returns:
            List of segment dictionaries with timing and amplitude information
        """
        # Calculate RR interval in seconds from heart rate
        rr_interval = 60.0 / self.heart_rate_bpm
        
        # Wide QRS complex (140ms) with large amplitude
        qrs = QRSComplex(
            duration_ms=140,  # 140ms wide QRS
            r_amplitude_mv=2.0,  # Large amplitude
            slurred=True
        )
        
        # Inverted T wave after QRS
        t_wave = TWave(
            duration=0.16,  # Slightly longer than QRS
            amplitude=-0.5,  # Inverted T wave
            positive=False
        )
        
        # No discernible P waves in VT
        
        return [
            # QRS complex
            {"start": 0.0, "end": qrs.duration, "segment": qrs},
            # ST segment (elevated in VT)
            {"start": qrs.duration, "end": qrs.duration + 0.1, "amplitude": 0.5},
            # T wave
            {"start": qrs.duration + 0.1, "end": qrs.duration + 0.1 + t_wave.duration, "segment": t_wave},
            # End of cycle (flat line until next QRS)
            {"start": qrs.duration + 0.1 + t_wave.duration, "end": rr_interval, "amplitude": 0.0}
        ]
    
    def apply_to_ecg(self, ecg):
        """Apply VT pattern to an ECG instance."""
        super().apply_to_ecg(ecg)
        # Add some baseline wander to make it look more realistic
        time = ecg.time
        ecg.voltage += 0.1 * np.sin(2 * np.pi * 0.2 * time)  # 0.2 Hz wander
