"""Sinus bradycardia pattern (heart rate < 60 bpm)."""

from typing import Dict, Optional

from .normal_sinus import NormalSinusRhythm


class SinusBradycardia(NormalSinusRhythm):
    """Sinus bradycardia rhythm (HR < 60 bpm).
    
    A normal sinus rhythm with a slower than normal heart rate.
    Common in athletes and during sleep. May be pathological if symptomatic.
    """
    
    def __init__(
        self,
        heart_rate_bpm: int = 50,
        duration_sec: float = 10.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
        rng_seed: Optional[int] = None,
    ):
        """Initialize sinus bradycardia rhythm.
        
        Args:
            heart_rate_bpm: Heart rate in bpm (should be < 60 bpm)
            duration_sec: Duration of the recording in seconds
            lead_modifiers: Optional dictionary of lead-specific modifications
            rng_seed: Optional random seed for reproducibility
            
        Raises:
            ValueError: If heart rate is not in bradycardic range
        """
        if heart_rate_bpm >= 60:
            raise ValueError(
                f"Sinus bradycardia requires HR < 60 bpm, got {heart_rate_bpm} bpm"
            )
            
        super().__init__(
            heart_rate_bpm=heart_rate_bpm,
            duration_sec=duration_sec,
            lead_modifiers=lead_modifiers,
            rng_seed=rng_seed,
        )
        self.name = f"Sinus Bradycardia ({heart_rate_bpm} bpm)"
