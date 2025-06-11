import unittest
import numpy as np
import matplotlib
matplotlib.use("Agg")

from cuddly_fiesta.clinical_validator import ClinicalValidator
from cuddly_fiesta.ecg_core import ECGCore, GridScaling
from cuddly_fiesta.waveform_segments import (
    AdvancedQRSComplex,
    AdvancedTWave,
    AdvancedNormalSinusRhythm,
)
from cuddly_fiesta.multi_lead import MultiLeadECG
from cuddly_fiesta.ecg_animation import animate_ecg


class TestAdvancedSegments(unittest.TestCase):
    def setUp(self):
        self.validator = ClinicalValidator()
        self.grid = GridScaling()

    def test_advanced_qrs_validation(self):
        qrs = AdvancedQRSComplex()
        valid_time, msg_time = self.validator.validate_timing("QRS_complex", qrs.duration_ms)
        self.assertTrue(valid_time, msg_time)
        valid_amp, msg_amp = self.validator.validate_amplitude("R_wave", abs(qrs.amplitude_mv))
        self.assertTrue(valid_amp, msg_amp)
        self.assertTrue(self.grid.validate_timing(qrs.duration_ms))

    def test_advanced_twave_validation(self):
        tw = AdvancedTWave()
        valid_time, msg_time = self.validator.validate_timing("T_wave", tw.duration_ms)
        self.assertTrue(valid_time, msg_time)
        valid_amp, msg_amp = self.validator.validate_amplitude("T_wave", abs(tw.amplitude_mv))
        self.assertTrue(valid_amp, msg_amp)
        self.assertTrue(self.grid.validate_timing(tw.duration_ms))


class TestAdvancedArrhythmia(unittest.TestCase):
    def test_per_lead_variation_grid_alignment(self):
        ecg = ECGCore(duration_sec=2, sampling_rate=1000)
        AdvancedNormalSinusRhythm().apply_to_ecg(ecg)
        ml = MultiLeadECG(ecg)
        grid = GridScaling()
        for info in ecg.segments_added:
            self.assertTrue(grid.validate_timing(info["start_time"] * 1000))
            self.assertTrue(grid.validate_timing(info["segment"].duration_ms))
        # ensure leads vary
        leads = list(ml.leads.values())
        self.assertTrue(any(not np.allclose(leads[0], ld) for ld in leads[1:]))

    def test_animation_smoke_multi_lead(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        AdvancedNormalSinusRhythm().apply_to_ecg(ecg)
        ml = MultiLeadECG(ecg)
        ani = animate_ecg(ml)
        self.assertIsNotNone(ani)


if __name__ == "__main__":
    unittest.main()
