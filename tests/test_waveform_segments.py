import unittest

import matplotlib

matplotlib.use("Agg")

from cuddly_fiesta.clinical_validator import ClinicalValidator
from cuddly_fiesta.ecg_animation import animate_ecg
from cuddly_fiesta.ecg_core import ECGCore, GridScaling
from cuddly_fiesta.multi_lead import MultiLeadECG
from cuddly_fiesta.waveform_segments import (
    AtrialFibrillation,
    AtrialFlutter,
    NormalSinusRhythm,
    TWave,
    UWave,
    VentricularTachycardia,
    VentricularFibrillation,
    PulselessElectricalActivity,
)


class TestWaves(unittest.TestCase):
    def setUp(self):
        self.validator = ClinicalValidator()
        self.grid = GridScaling()

    def test_twave_defaults(self):
        tw = TWave()
        valid_timing, msg_timing = self.validator.validate_timing(
            "T_wave", tw.duration_ms
        )
        self.assertTrue(valid_timing, msg_timing)
        valid_amp, msg_amp = self.validator.validate_amplitude(
            "T_wave", abs(tw.amplitude_mv)
        )
        self.assertTrue(valid_amp, msg_amp)
        self.assertTrue(self.grid.validate_timing(tw.duration_ms))

    def test_uwave_defaults(self):
        uw = UWave()
        valid_timing, msg_timing = self.validator.validate_timing(
            "U_wave", uw.duration_ms
        )
        self.assertTrue(valid_timing, msg_timing)
        valid_amp, msg_amp = self.validator.validate_amplitude(
            "U_wave", abs(uw.amplitude_mv)
        )
        self.assertTrue(valid_amp, msg_amp)
        self.assertTrue(self.grid.validate_timing(uw.duration_ms))


class TestArrhythmiaPatterns(unittest.TestCase):
    def _check_pattern(self, pattern):
        ecg = ECGCore(duration_sec=3, sampling_rate=1000)
        pattern.apply_to_ecg(ecg)
        grid = GridScaling()
        for info in ecg.segments_added:
            self.assertTrue(
                grid.validate_timing(info["start_time"] * 1000),
                f"Segment {info['segment'].__class__.__name__} start time {info['start_time']:.3f}s not grid aligned",
            )
            seg = info["segment"]
            self.assertTrue(
                grid.validate_timing(seg.duration_ms),
                f"Segment {seg.__class__.__name__} duration {seg.duration_ms}ms not grid aligned",
            )

    def test_all_patterns_grid_alignment(self):
        self._check_pattern(NormalSinusRhythm())
        self._check_pattern(AtrialFibrillation())
        self._check_pattern(AtrialFlutter())
        self._check_pattern(VentricularTachycardia())
        self._check_pattern(VentricularFibrillation())
        self._check_pattern(PulselessElectricalActivity())


class TestMultiLeadAndAnimation(unittest.TestCase):
    def test_multi_lead_shapes(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm().apply_to_ecg(ecg)
        ml = MultiLeadECG.from_ecg(ecg)
        self.assertEqual(len(ml.leads), 12)
        for lead in ml.leads.values():
            self.assertEqual(len(lead), len(ecg.time))

    def test_animation_smoke(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm().apply_to_ecg(ecg)
        ani1 = animate_ecg(ecg, show_grid=True)
        self.assertIsNotNone(ani1)
        ml = MultiLeadECG.from_ecg(ecg)
        ani2 = animate_ecg(ml, show_grid=True)
        self.assertIsNotNone(ani2)


if __name__ == "__main__":
    unittest.main()
