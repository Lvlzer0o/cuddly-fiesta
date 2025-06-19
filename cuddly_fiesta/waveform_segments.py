from __future__ import annotations

from typing import List, Dict

from .core import ArrhythmiaPattern
from .segments import PWave, QRSComplex, TWave, UWave
from .rhythms import (
    NormalSinusRhythm,
    AtrialFibrillation,
    VentricularTachycardia,
    WolffParkinsonWhite,
)

# Optional rhythm that does not yet have a full implementation
try:  # pragma: no cover - optional component
    from .rhythms.pericarditis import Pericarditis
except Exception:  # pragma: no cover - keep import flexible
    Pericarditis = None


class VentricularFibrillation(ArrhythmiaPattern):
    """Minimal placeholder pattern used for tests."""

    def __init__(self) -> None:
        super().__init__("Ventricular Fibrillation")

    def define_pattern(self) -> List[Dict]:
        return []


class PulselessElectricalActivity(ArrhythmiaPattern):
    """Represents an isoelectric rhythm for testing purposes."""

    def __init__(self) -> None:
        super().__init__("Pulseless Electrical Activity")

    def define_pattern(self) -> List[Dict]:
        return []


__all__ = [
    "ArrhythmiaPattern",
    "NormalSinusRhythm",
    "AtrialFibrillation",
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

