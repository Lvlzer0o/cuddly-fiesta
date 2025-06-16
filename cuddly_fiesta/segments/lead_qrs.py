"""Lead-specific QRS complex segments."""

from typing import Dict, Optional
from .qrs_complex import QRSComplex


class LeadQRSComplex(QRSComplex):
    """QRS complex scaled for a specific lead orientation.
    
    Applies lead-specific scaling and polarity to the base QRS complex.
    """
    
    def __init__(
        self,
        lead: str,
        amplitude_scale: float = 1.0,
        polarity: float = 1.0,
        axis_deg: float = 0.0,
        **kwargs,
    ):
        """Initialize lead-specific QRS complex.
        
        Args:
            lead: Lead name (e.g., 'I', 'II', 'V1', etc.)
            amplitude_scale: Scaling factor for amplitude (0.5-1.5)
            polarity: Polarity multiplier (1.0 or -1.0)
            axis_deg: Electrical axis in degrees (0-360)
            **kwargs: Additional arguments passed to QRSComplex
        """
        # Apply lead-specific scaling and polarity
        base_amp = (
            kwargs.get("r_amplitude_mv", 1.0)
            * amplitude_scale
            * polarity
            * np.cos(np.radians(axis_deg))
        )
        
        # Update amplitude in kwargs
        kwargs["r_amplitude_mv"] = base_amp
        
        # Initialize base class
        super().__init__(**kwargs)
        
        # Store lead-specific parameters
        self.lead = lead
        self.amplitude_scale = amplitude_scale
        self.polarity = polarity
        self.axis_deg = axis_deg
