"""Sinus tachycardia pattern (heart rate > 100 bpm)."""

from typing import Dict, Optional

from .normal_sinus import NormalSinusRhythm


class SinusTachycardia(NormalSinusRhythm):
    """Sinus tachycardia rhythm (HR > 100 bpm).
    
    A normal sinus rhythm with a faster than normal heart rate.
    Common during exercise, stress, fever, or other physiological stress.
    """
    
    def __init__(
        self,
        heart_rate_bpm: int = 120,
        duration_sec: float = 10.0,
        lead_modifiers: Optional[Dict[str, Dict]] = None,
        rng_seed: Optional[int] = None,
    ):
        """Initialize sinus tachycardia rhythm.
        
        Args:
            heart_rate_bpm: Heart rate in bpm (should be > 100 bpm)
            duration_sec: Duration of the recording in seconds
            lead_modifiers: Optional dictionary of lead-specific modifications
            rng_seed: Optional random seed for reproducibility
            
        Raises:
            ValueError: If heart rate is not in tachycardic range
        """
        if heart_rate_bpm <= 100:
            raise ValueError(
                f"Sinus tachycardia requires HR > 100 bpm, got {heart_rate_bpm} bpm"
            )
            
        super().__init__(
            heart_rate_bpm=heart_rate_bpm,
            duration_sec=duration_sec,
            lead_modifiers=lead_modifiers,
            rng_seed=rng_seed,
        )
        self.name = f"Sinus Tachycardia ({heart_rate_bpm} bpm)"
