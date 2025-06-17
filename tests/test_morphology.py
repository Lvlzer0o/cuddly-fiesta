import unittest
import numpy as np

from cuddly_fiesta.ecg_core import ECGCore
from cuddly_fiesta.waveform_segments import NormalSinusRhythm
from cuddly_fiesta.multi_lead import MultiLeadECG


class TestLeadMorphology(unittest.TestCase):
    def test_per_lead_qrs_scaling(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm().apply_to_ecg(ecg)
        morph = {"V1": {"QRS": {"r_scale": 0.5}}, "V5": {"QRS": {"r_scale": 1.5}}}
        ml = MultiLeadECG.from_ecg(ecg, morphology=morph)
        amp_v1 = np.max(np.abs(ml.get_lead("V1")))
        amp_v5 = np.max(np.abs(ml.get_lead("V5")))
        self.assertLess(amp_v1, amp_v5)


if __name__ == "__main__":
    unittest.main()
