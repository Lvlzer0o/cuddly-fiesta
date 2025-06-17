from __future__ import annotations

from typing import List, Dict

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
run = importlib.import_module("run")

ArrhythmiaPattern = run.ArrhythmiaPattern
NormalSinusRhythm = run.NormalSinusRhythm
AtrialFibrillation = run.AtrialFibrillation
VentricularTachycardia = run.VentricularTachycardia
WolffParkinsonWhite = run.WolffParkinsonWhite
Pericarditis = run.Pericarditis
PWave = run.PWave
QRSComplex = run.QRSComplex
TWave = run.TWave
UWave = run.UWave


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

