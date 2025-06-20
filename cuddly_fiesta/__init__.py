"""Minimal stubs exposing the public API used in the tests."""

from . import agents
from .clinical_validator import ClinicalValidator
from .ecg_core import ECGCore, GridScaling
from .multi_lead import MultiLeadECG
from .ecg_animation import animate_ecg
from .p_wave_generator import PWaveGenerator
from .waveform_segments import (
    ArrhythmiaPattern,
    NormalSinusRhythm,
    AtrialFibrillation,
    AtrialFlutter,
    VentricularTachycardia,
    VentricularFibrillation,
    PulselessElectricalActivity,
    WolffParkinsonWhite,
    Pericarditis,
    PWave,
    QRSComplex,
    TWave,
    UWave,
)

__all__ = [
    "agents",
    "ClinicalValidator",
    "ECGCore",
    "GridScaling",
    "MultiLeadECG",
    "animate_ecg",
    "PWaveGenerator",
    "ArrhythmiaPattern",
    "NormalSinusRhythm",
    "AtrialFibrillation",
    "AtrialFlutter",
    "VentricularTachycardia",
    "VentricularFibrillation",
    "PulselessElectricalActivity",
    "WolffParkinsonWhite",
    "Pericarditis",
    "PWave",
    "QRSComplex",
    "TWave",
    "UWave",
]
