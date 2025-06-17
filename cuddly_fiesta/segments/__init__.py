"""Waveform segment primitives for ECG generation.

This package contains all the waveform segments used to construct ECG patterns,
including individual waves (P, QRS, T, U) and lead-specific variants.
"""

# The full project exposes ``WaveformSegment`` from a ``core`` package. In this
# trimmed test fixture the implementation lives in ``run.py`` at the repository
# root, so we load it dynamically.
import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
WaveformSegment = importlib.import_module("run").WaveformSegment
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
