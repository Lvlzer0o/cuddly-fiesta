"""Waveform segment primitives for ECG generation.

This package contains all the waveform segments used to construct ECG patterns,
including individual waves (P, QRS, T, U) and lead-specific variants.
"""

from ..core import WaveformSegment
from .p_wave import PWave
from .qrs_complex import QRSComplex
from .t_wave import TWave
from .u_wave import UWave
from .lead_qrs import LeadQRSComplex
from .lead_t_wave import LeadTWave

__all__ = [
    "WaveformSegment",
    "PWave",
    "QRSComplex",
    "TWave",
    "UWave",
    "LeadQRSComplex",
    "LeadTWave",
]
