from __future__ import annotations

from typing import List, Dict, Optional
import numpy as np

from .base import ArrhythmiaPattern
from ..segments import PWave, PRSegment, QRSComplex, STSegment, TWave, UWave

class WolffParkinsonWhite(ArrhythmiaPattern):
    """WPW (Wolff-Parkinson-White) pattern with short PR and delta wave."""

    def __init__(self, heart_rate_bpm: int = 80) -> None:
        super().__init__("Wolff-Parkinson-White")
        self.heart_rate_bpm = heart_rate_bpm

    def define_pattern(self) -> List[Dict]:
        """Define the WPW pattern with characteristic delta waves.
        
        Returns:
            List of segment dictionaries with timing and amplitude information
        """
        # Calculate RR interval in seconds from heart rate
        rr_interval = 60.0 / self.heart_rate_bpm
        
        # Normal P wave
        p_wave = PWave(
            duration=0.08,  # 80ms
            amplitude=0.15,
            positive=True
        )
        
        # Short PR interval (<120ms)
        pr_segment = PRSegment(
            duration=0.10,  # 100ms (normal is 120-200ms)
            amplitude=0.0
        )
        
        # QRS with delta wave (slurred upstroke)
        qrs = QRSComplex(
            duration_ms=120,  # Slightly wide QRS (normal is <100ms)
            r_amplitude_mv=1.5,
            slurred=True,  # Creates the delta wave effect
            delta_wave_duration_ms=40  # Duration of the delta wave in ms
        )
        
        # ST segment may be depressed
        st_segment = STSegment(
            duration=0.12,
            amplitude=-0.05  # Slight depression
        )
        
        # T wave may be inverted in WPW
        t_wave = TWave(
            duration=0.16,
            amplitude=0.3,
            positive=False  # Inverted T wave
        )
        
        return [
            # P wave
            {"start": 0.0, "end": p_wave.duration, "segment": p_wave},
            # PR segment (shortened)
            {"start": p_wave.duration, "end": p_wave.duration + pr_segment.duration, "segment": pr_segment},
            # QRS with delta wave
            {"start": p_wave.duration + pr_segment.duration, 
              "end": p_wave.duration + pr_segment.duration + qrs.duration, 
              "segment": qrs},
            # ST segment
            {"start": p_wave.duration + pr_segment.duration + qrs.duration,
              "end": p_wave.duration + pr_segment.duration + qrs.duration + st_segment.duration,
              "segment": st_segment},
            # T wave
            {"start": p_wave.duration + pr_segment.duration + qrs.duration + st_segment.duration,
              "end": p_wave.duration + pr_segment.duration + qrs.duration + st_segment.duration + t_wave.duration,
              "segment": t_wave},
            # End of cycle
            {"start": p_wave.duration + pr_segment.duration + qrs.duration + st_segment.duration + t_wave.duration,
              "end": rr_interval,
              "amplitude": 0.0}
        ]
    
    def apply_to_ecg(self, ecg):
        """Apply WPW pattern to an ECG instance."""
        super().apply_to_ecg(ecg)
        # Add subtle baseline wander for realism
        time = ecg.time
        ecg.voltage += 0.05 * np.sin(2 * np.pi * 0.1 * time)  # Very subtle wander
