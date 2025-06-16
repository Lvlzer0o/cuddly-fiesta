"""Arrhythmia rhythm patterns for ECG generation.

This package contains implementations of various cardiac arrhythmia patterns
that can be used to generate realistic ECG signals. Each pattern is implemented
as a class that defines the timing and morphology of the ECG waveform.
"""
from __future__ import annotations

from typing import Dict, Optional, Type, Union, Any

# Import base class first
from ..core import ArrhythmiaPattern

# Import rhythm classes from their respective modules
from .normal_sinus import NormalSinusRhythm
from .sinus_bradycardia import SinusBradycardia
from .sinus_tachycardia import SinusTachycardia
from .atrial_fibrillation import AtrialFibrillation
from .asystole import Asystole
from .first_degree_av_block import FirstDegreeAVBlock
from .third_degree_av_block import ThirdDegreeAVBlock
from .bundle_branch_block import BundleBranchBlock
from .supraventricular_tachycardia import SupraventricularTachycardia
from .multifocal_atrial_tachycardia import MultifocalAtrialTachycardia
from .ventricular_fibrillation import VentricularFibrillation
from .torsades_de_pointes import TorsadesDePointes

# TODO: Import other rhythm classes as they are implemented
# from .atrial_flutter import AtrialFlutter
# from .ventricular_tachycardia import VentricularTachycardia
# from .premature_ventricular_contraction import PrematureVentricularContraction
# from .second_degree_av_block import SecondDegreeAVBlock

# Re-export all rhythm classes
__all__ = [
    "ArrhythmiaPattern",
    "NormalSinusRhythm",
    "SinusBradycardia",
    "SinusTachycardia",
    "AtrialFibrillation",
    "Asystole",
    "FirstDegreeAVBlock",
    "ThirdDegreeAVBlock",
    "BundleBranchBlock",
    "SupraventricularTachycardia",
    "MultifocalAtrialTachycardia",
    "VentricularFibrillation",
    "TorsadesDePointes",
    # "AtrialFlutter",
    # "VentricularTachycardia",
    # "PrematureVentricularContraction",
    # "SecondDegreeAVBlock",
]
