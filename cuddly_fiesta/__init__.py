"""ECG generation and visualization tools."""

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


def run_visualizer():
    from .ecg_visualizer import run_visualizer as _run_visualizer

    return _run_visualizer()


def __getattr__(name):
    if name == "ECGVisualizer":
        from .ecg_visualizer import ECGVisualizer

        return ECGVisualizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "agents",
    "ClinicalValidator",
    "ECGCore",
    "GridScaling",
    "MultiLeadECG",
    "animate_ecg",
    "ECGVisualizer",
    "run_visualizer",
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
