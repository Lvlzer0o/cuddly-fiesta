"""Core ECG generation functionality.

This package contains the core classes for generating and manipulating
ECG signals with proper grid scaling and validation.
"""

from .grid_scaling import GridScaling
from .waveform_segment import WaveformSegment
from .arrhythmia_pattern import ArrhythmiaPattern
from .ecg_core import ECGCore
from .multi_lead import MultiLeadECG
from .clinical_validator import ClinicalValidator

__all__ = [
    'GridScaling',
    'WaveformSegment',
    'ArrhythmiaPattern',
    'ECGCore',
    'MultiLeadECG',
    'ClinicalValidator',
]
