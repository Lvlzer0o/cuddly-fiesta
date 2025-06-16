"""Lead-specific T-wave segments."""

import numpy as np
from typing import Dict, Optional
from .t_wave import TWave


class LeadTWave(TWave):
    """T-wave scaled for a specific lead orientation.
    
    Applies lead-specific scaling and polarity to the base T-wave.
    """
    
    def __init__(
        self,
        lead: str,
        amplitude_scale: float = 1.0,
        polarity: float = 1.0,
        axis_deg: float = 0.0,
        **kwargs,
    ):
        """Initialize lead-specific T-wave.
        
        Args:
            lead: Lead name (e.g., 'I', 'II', 'V1', etc.)
            amplitude_scale: Scaling factor for amplitude (0.5-1.5)
            polarity: Polarity multiplier (1.0 or -1.0)
            axis_deg: Electrical axis in degrees (0-360)
            **kwargs: Additional arguments passed to TWave
        """
        # Apply lead-specific scaling and polarity
        base_amp = (
            kwargs.get("amplitude_mv", 0.25)
            * amplitude_scale
            * polarity
            * np.cos(np.radians(axis_deg))
        )
        
        # Update amplitude in kwargs
        kwargs["amplitude_mv"] = base_amp
        
        # Initialize base class
        super().__init__(**kwargs)
        
        # Store lead-specific parameters
        self.lead = lead
        self.amplitude_scale = amplitude_scale
        self.polarity = polarity
        self.axis_deg = axis_deg
