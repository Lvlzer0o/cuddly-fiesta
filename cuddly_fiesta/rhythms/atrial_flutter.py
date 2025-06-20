"""Simple atrial flutter rhythm pattern."""

from __future__ import annotations

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import PWave, QRSComplex, TWave


class AtrialFlutter(ArrhythmiaPattern):
    """Generates a basic atrial flutter rhythm with sawtooth F-waves.

    This implementation uses rapidly repeating P-waves to approximate the
    classic "sawtooth" flutter waves.  QRS complexes are inserted according
    to the specified conduction ratio.
    """

    def __init__(
        self,
        atrial_rate_bpm: float = 300.0,
        conduction_ratio: int = 2,
        duration_sec: float = 10.0,
        lead_modifiers: dict | None = None,
    ) -> None:
        super().__init__("Atrial Flutter", lead_modifiers)
        if not (200 <= atrial_rate_bpm <= 350):
            raise ValueError("Atrial flutter rate must be 200-350 bpm")
        if conduction_ratio < 1:
            raise ValueError("Conduction ratio must be >= 1")
        self.atrial_rate_bpm = atrial_rate_bpm
        self.conduction_ratio = conduction_ratio
        self.duration_sec = duration_sec

    def define_pattern(self) -> None:
        self.segments = []
        atrial_interval = 60.0 / self.atrial_rate_bpm
        time = 0.0
        beat_count = 0

        while time < self.duration_sec:
            f_wave = PWave(amplitude_mv=0.1, duration_ms=80)
            self.add_segment(time, f_wave)
            beat_count += 1
            if beat_count % self.conduction_ratio == 0:
                qrs_start = time + 0.12
                qrs = QRSComplex(duration_ms=100)
                self.add_segment(qrs_start, qrs)
                t_start = qrs_start + 0.28
                t_wave = TWave(duration_ms=160)
                self.add_segment(t_start, t_wave)
            time += atrial_interval
