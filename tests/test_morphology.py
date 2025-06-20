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

    def test_pwave_orientation(self):
        ecg = ECGCore(duration_sec=2, sampling_rate=1000)
        NormalSinusRhythm(heart_rate_bpm=60).apply_to_ecg(ecg)
        ml = MultiLeadECG.from_ecg(ecg)

        p_info = next(
            s for s in ecg.segments_added if s["segment"].__class__.__name__ == "PWave"
        )
        start = p_info["start_time"]
        dur = p_info["segment"].duration_ms / 1000
        mask = (ecg.time >= start) & (ecg.time < start + dur)

        lead_I = ml.get_lead("I")[mask]
        lead_II = ml.get_lead("II")[mask]
        lead_aVR = ml.get_lead("aVR")[mask]
        lead_III = ml.get_lead("III")[mask]
        lead_aVL = ml.get_lead("aVL")[mask]
        lead_aVF = ml.get_lead("aVF")[mask]
        lead_V4 = ml.get_lead("V4")[mask]
        lead_V5 = ml.get_lead("V5")[mask]
        lead_V6 = ml.get_lead("V6")[mask]

        self.assertGreater(lead_I.max(), abs(lead_I.min()))
        self.assertGreater(lead_II.max(), abs(lead_II.min()))
        self.assertGreater(abs(lead_aVR.min()), lead_aVR.max())
        self.assertGreater(lead_III.max(), abs(lead_III.min()))
        self.assertGreater(lead_aVL.max(), abs(lead_aVL.min()))
        self.assertGreater(lead_aVF.max(), abs(lead_aVF.min()))
        self.assertGreater(lead_V4.max(), abs(lead_V4.min()))
        self.assertGreater(lead_V5.max(), abs(lead_V5.min()))
        self.assertGreater(lead_V6.max(), abs(lead_V6.min()))


if __name__ == "__main__":
    unittest.main()
