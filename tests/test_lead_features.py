import unittest
import numpy as np

from cuddly_fiesta import ClinicalValidator, ECGCore, MultiLeadECG
from cuddly_fiesta.waveform_segments import WolffParkinsonWhite

class TestLeadConstraints(unittest.TestCase):
    def test_r_wave_lead_ranges(self):
        v = ClinicalValidator()
        ok_v1, _ = v.validate_amplitude("R_wave", 0.5, lead="V1")
        bad_v1, _ = v.validate_amplitude("R_wave", 2.0, lead="V1")
        self.assertTrue(ok_v1)
        self.assertFalse(bad_v1)

class TestLeadMorphology(unittest.TestCase):
    def test_wpw_per_lead_override(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        pattern = WolffParkinsonWhite()
        pattern.apply_to_ecg(ecg)
        ml_normal = MultiLeadECG.from_ecg(ecg)
        ml_wpw = MultiLeadECG.from_ecg(ecg, morphology=pattern.get_lead_morphology())
        amp_norm = np.max(np.abs(ml_normal.get_lead("V2")))
        amp_wpw = np.max(np.abs(ml_wpw.get_lead("V2")))
        self.assertGreater(amp_wpw, amp_norm)

if __name__ == "__main__":
    unittest.main()
