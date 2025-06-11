import unittest
import matplotlib
matplotlib.use("Agg")

from clinical_validator import ClinicalValidator
from ecg_core import ECGCore, GridScaling
from waveform_segments import (
    TWave,
    UWave,
    NormalSinusRhythm,
    AtrialFibrillation,
    VentricularTachycardia,
)
from multi_lead import MultiLeadECG
from ecg_animation import animate_ecg


class TestWaves(unittest.TestCase):
    def setUp(self):
        self.validator = ClinicalValidator()
        self.grid = GridScaling()

    def test_twave_defaults(self):
        tw = TWave()
        self.assertTrue(self.validator.validate_timing("T_wave", tw.duration_ms)[0])
        self.assertTrue(self.validator.validate_amplitude("T_wave", abs(tw.amplitude_mv))[0])
        self.assertTrue(self.grid.validate_timing(tw.duration_ms))

    def test_uwave_defaults(self):
        uw = UWave()
        self.assertTrue(self.validator.validate_timing("U_wave", uw.duration_ms)[0])
        self.assertTrue(self.validator.validate_amplitude("U_wave", abs(uw.amplitude_mv))[0])
        self.assertTrue(self.grid.validate_timing(uw.duration_ms))


class TestArrhythmiaPatterns(unittest.TestCase):
    def _check_pattern(self, pattern):
        ecg = ECGCore(duration_sec=3, sampling_rate=1000)
        pattern.apply_to_ecg(ecg)
        grid = GridScaling()
        for info in ecg.segments_added:
            self.assertTrue(grid.validate_timing(info["start_time"] * 1000))
            seg = info["segment"]
            self.assertTrue(grid.validate_timing(seg.duration_ms))

    def test_all_patterns_grid_alignment(self):
        self._check_pattern(NormalSinusRhythm())
        self._check_pattern(AtrialFibrillation())
        self._check_pattern(VentricularTachycardia())


class TestMultiLeadAndAnimation(unittest.TestCase):
    def test_multi_lead_shapes(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm().apply_to_ecg(ecg)
        ml = MultiLeadECG(ecg)
        self.assertEqual(len(ml.leads), 12)
        for lead in ml.leads.values():
            self.assertEqual(len(lead), len(ecg.time))

    def test_animation_smoke(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm().apply_to_ecg(ecg)
        ani1 = animate_ecg(ecg)
        self.assertIsNotNone(ani1)
        ml = MultiLeadECG(ecg)
        ani2 = animate_ecg(ml)
        self.assertIsNotNone(ani2)


if __name__ == "__main__":
    unittest.main()
