from __future__ import annotations

from typing import List, Dict

from .base import ArrhythmiaPattern


class VentricularTachycardia(ArrhythmiaPattern):
    """Minimal placeholder ventricular tachycardia pattern."""

    def __init__(self) -> None:
        super().__init__("Ventricular Tachycardia")

    def define_pattern(self) -> List[Dict]:
        return []
