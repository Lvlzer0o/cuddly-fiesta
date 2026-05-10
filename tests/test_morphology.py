import unittest
import numpy as np

from cuddly_fiesta.ecg_core import ECGCore
from cuddly_fiesta.waveform_segments import NormalSinusRhythm, PWave, QRSComplex
from cuddly_fiesta.multi_lead import MultiLeadECG
from cuddly_fiesta.rhythms import BundleBranchBlock


class TestLeadMorphology(unittest.TestCase):
    @staticmethod
    def _peak_to_peak(signal):
        return float(np.max(signal) - np.min(signal))

    @staticmethod
    def _first_qrs_window(ecg):
        qrs_event = next(
            event for event in ecg.segments_added
            if event["component_type"] == "QRSComplex"
        )
        start = qrs_event["start_time"]
        end = start + qrs_event["segment"].duration_ms / 1000.0
        return qrs_event, (ecg.time >= start) & (ecg.time < end)

    def test_events_record_component_metadata(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        ecg.add_waveform_segment(PWave(), 0.12)

        event = ecg.segments_added[0]

        self.assertEqual(event["component_type"], "PWave")
        self.assertEqual(event["timing"]["start_sec"], event["start_time"])
        self.assertEqual(event["timing"]["duration_ms"], event["segment"].duration_ms)
        self.assertEqual(event["shape"]["class_name"], "PWave")
        self.assertIn("degrees", event["axis"])
        self.assertIn("profile", event["lead_profile"])

    def test_multi_lead_synthesizes_from_events_not_scalar_voltage(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        ecg.add_waveform_segment(QRSComplex(), 0.24)
        ecg.voltage[:] = 0.0

        ml = MultiLeadECG.from_ecg(ecg)

        self.assertGreater(np.max(np.abs(ml.get_lead("II"))), 0.5)

    def test_component_modifier_does_not_scale_unrelated_waves(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        ecg.add_waveform_segment(PWave(), 0.04)
        ecg.add_waveform_segment(QRSComplex(), 0.40)

        base = MultiLeadECG.from_ecg(ecg)
        modified = MultiLeadECG.from_ecg(
            ecg, morphology={"II": {"QRS": {"r_scale": 2.0}}}
        )

        p_event = ecg.segments_added[0]
        qrs_event = ecg.segments_added[1]
        p_mask = (ecg.time >= p_event["start_time"]) & (
            ecg.time < p_event["start_time"] + p_event["segment"].duration_ms / 1000
        )
        qrs_mask = (ecg.time >= qrs_event["start_time"]) & (
            ecg.time < qrs_event["start_time"] + qrs_event["segment"].duration_ms / 1000
        )

        base_p = self._peak_to_peak(base.get_lead("II")[p_mask])
        modified_p = self._peak_to_peak(modified.get_lead("II")[p_mask])
        base_qrs = self._peak_to_peak(base.get_lead("II")[qrs_mask])
        modified_qrs = self._peak_to_peak(modified.get_lead("II")[qrs_mask])

        self.assertAlmostEqual(modified_p, base_p, delta=0.01)
        self.assertGreater(modified_qrs, base_qrs * 1.5)

    def test_rhythm_lead_modifiers_feed_multi_lead_synthesis(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        pattern = NormalSinusRhythm(
            heart_rate_bpm=60,
            duration_sec=1,
            lead_modifiers={"II": {"QRS": {"r_scale": 2.0}}},
            rng_seed=1,
        )
        pattern.apply_to_ecg(ecg)

        base = MultiLeadECG.from_ecg(ecg, morphology={"II": {}})
        modified = MultiLeadECG.from_ecg(ecg)

        qrs_event = next(
            event for event in ecg.segments_added
            if event["component_type"] == "QRSComplex"
        )
        qrs_mask = (ecg.time >= qrs_event["start_time"]) & (
            ecg.time < qrs_event["start_time"] + qrs_event["segment"].duration_ms / 1000
        )

        base_qrs = self._peak_to_peak(base.get_lead("II")[qrs_mask])
        modified_qrs = self._peak_to_peak(modified.get_lead("II")[qrs_mask])

        self.assertGreater(modified_qrs, base_qrs * 1.5)

    def test_empty_morphology_overrides_rhythm_modifiers(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        pattern = NormalSinusRhythm(
            heart_rate_bpm=60,
            duration_sec=1,
            lead_modifiers={"II": {"QRS": {"r_scale": 2.0}}},
            rng_seed=1,
        )
        pattern.apply_to_ecg(ecg)

        suppressed = MultiLeadECG.from_ecg(ecg, morphology={})
        per_lead_suppressed = MultiLeadECG.from_ecg(ecg, morphology={"II": {}})
        modified = MultiLeadECG.from_ecg(ecg)

        qrs_event = next(
            event for event in ecg.segments_added
            if event["component_type"] == "QRSComplex"
        )
        qrs_mask = (ecg.time >= qrs_event["start_time"]) & (
            ecg.time < qrs_event["start_time"] + qrs_event["segment"].duration_ms / 1000
        )

        suppressed_qrs = self._peak_to_peak(suppressed.get_lead("II")[qrs_mask])
        per_lead_suppressed_qrs = self._peak_to_peak(
            per_lead_suppressed.get_lead("II")[qrs_mask]
        )
        modified_qrs = self._peak_to_peak(modified.get_lead("II")[qrs_mask])

        self.assertAlmostEqual(suppressed_qrs, per_lead_suppressed_qrs, delta=0.01)
        self.assertGreater(modified_qrs, suppressed_qrs * 1.5)

    def test_per_lead_qrs_scaling(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        NormalSinusRhythm().apply_to_ecg(ecg)
        morph = {"V1": {"QRS": {"r_scale": 0.5}}, "V5": {"QRS": {"r_scale": 1.5}}}
        ml = MultiLeadECG.from_ecg(ecg, morphology=morph)
        amp_v1 = np.max(np.abs(ml.get_lead("V1")))
        amp_v5 = np.max(np.abs(ml.get_lead("V5")))
        self.assertLess(amp_v1, amp_v5)

    def test_rbbb_template_has_v1_r_prime_and_lateral_terminal_s(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        BundleBranchBlock(
            heart_rate_bpm=60,
            duration_sec=1,
            qrs_duration_ms=140,
            block_type="right",
        ).apply_to_ecg(ecg)
        ml = MultiLeadECG.from_ecg(ecg)

        qrs_event, qrs_mask = self._first_qrs_window(ecg)
        v1_qrs = ml.get_lead("V1")[qrs_mask]
        v6_qrs = ml.get_lead("V6")[qrs_mask]
        terminal_start = int(len(v1_qrs) * 0.65)

        self.assertEqual(qrs_event["lead_profile"]["profile"], "rbbb")
        self.assertGreater(v1_qrs[terminal_start:].max(), v1_qrs[:terminal_start].max())
        self.assertGreater(abs(v6_qrs[terminal_start:].min()), v6_qrs[terminal_start:].max())

    def test_lbbb_template_has_negative_v1_and_broad_positive_v6(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        BundleBranchBlock(
            heart_rate_bpm=60,
            duration_sec=1,
            qrs_duration_ms=150,
            block_type="left",
        ).apply_to_ecg(ecg)
        ml = MultiLeadECG.from_ecg(ecg)

        qrs_event, qrs_mask = self._first_qrs_window(ecg)
        v1_qrs = ml.get_lead("V1")[qrs_mask]
        v6_qrs = ml.get_lead("V6")[qrs_mask]
        terminal_start = int(len(v6_qrs) * 0.55)

        self.assertEqual(qrs_event["lead_profile"]["profile"], "lbbb")
        self.assertGreater(abs(v1_qrs.min()), v1_qrs.max() * 1.5)
        self.assertGreater(v6_qrs.max(), abs(v6_qrs.min()) * 2.0)
        self.assertGreater(v6_qrs[terminal_start:].max(), 0.2)

    def test_bbb_template_keeps_standard_projection_for_untemplated_leads(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        BundleBranchBlock(
            heart_rate_bpm=60,
            duration_sec=1,
            qrs_duration_ms=140,
            block_type="right",
        ).apply_to_ecg(ecg)
        ml = MultiLeadECG.from_ecg(ecg)

        qrs_event, qrs_mask = self._first_qrs_window(ecg)
        _, base_qrs = qrs_event["segment"].generate(ecg.sampling_rate)
        lead_ii_qrs = ml.get_lead("II")[qrs_mask]

        self.assertAlmostEqual(lead_ii_qrs.max(), base_qrs.max() * 1.5, delta=0.01)

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
