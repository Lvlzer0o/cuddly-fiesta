"""Simple atrial flutter rhythm pattern."""

from __future__ import annotations

import numpy as np

from ..core import ArrhythmiaPattern, ECGCore
from ..segments import PWave, QRSComplex, TWave


class AtrialFlutter(ArrhythmiaPattern):
    """Generates a basic atrial flutter rhythm with sawtooth F-waves.

    Parameters
    ----------
    atrial_rate_bpm : float
        Rate of the atrial "flutter" activity. Typical flutter ranges from
        200-350 bpm.
    conduction_ratio : int
        Number of flutter waves per conducted QRS complex (e.g. 2 for 2:1).
    duration_sec : float
        Total length of the generated rhythm strip.
    lead_modifiers : dict | None
        Optional per-lead scaling or morphology adjustments.
    qrs_offset_ms : float
        Time delay from an F-wave to the ensuing QRS complex when conduction
        occurs.
    t_offset_ms : float
        Time delay from the QRS complex to the following T-wave.
    """

    def __init__(
        self,
        atrial_rate_bpm: float = 300.0,
        conduction_ratio: int = 2,
        duration_sec: float = 10.0,
        lead_modifiers: dict | None = None,
        qrs_offset_ms: float = 120.0,
        t_offset_ms: float = 280.0,
    ) -> None:
        super().__init__("Atrial Flutter", lead_modifiers)
        # Typical atrial flutter occurs between 200-350 bpm; outside this range
        # suggests another rhythm or atypical physiology.
        if not (200 <= atrial_rate_bpm <= 350):
            raise ValueError("Atrial flutter rate must be 200-350 bpm")
        if conduction_ratio < 1:
            raise ValueError("Conduction ratio must be >= 1")
        self.atrial_rate_bpm = atrial_rate_bpm
        self.conduction_ratio = conduction_ratio
        self.duration_sec = duration_sec
        self.qrs_offset_ms = qrs_offset_ms
        self.t_offset_ms = t_offset_ms

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
                qrs_start = time + self.qrs_offset_ms / 1000.0
                qrs = QRSComplex(duration_ms=100)
                self.add_segment(qrs_start, qrs)
                t_start = qrs_start + self.t_offset_ms / 1000.0
                t_wave = TWave(duration_ms=160)
                self.add_segment(t_start, t_wave)
            time += atrial_interval
