import unittest

import matplotlib

matplotlib.use("Agg")
import numpy as np

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
from cuddly_fiesta.rhythms import (
    Asystole,
    BundleBranchBlock,
    FirstDegreeAVBlock,
    MultifocalAtrialTachycardia,
    SupraventricularTachycardia,
    ThirdDegreeAVBlock,
    TorsadesDePointes,
    VentricularFibrillation as RhythmVentricularFibrillation,
    WolffParkinsonWhite,
)


def _events_by_type(ecg, component_type):
    return [
        event for event in ecg.segments_added
        if event["component_type"] == component_type
    ]


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
        for info in ecg.segments_added:
            seg = info["segment"]
            self.assertGreaterEqual(info["start_time"], 0)
            self.assertLess(info["start_time"], ecg.duration_sec)
            self.assertGreater(seg.duration_ms, 0)
            self.assertEqual(info["component_type"], seg.__class__.__name__)
            self.assertEqual(info["timing"]["duration_ms"], seg.duration_ms)

    def test_all_patterns_grid_alignment(self):
        self._check_pattern(NormalSinusRhythm())
        self._check_pattern(AtrialFibrillation())
        self._check_pattern(AtrialFlutter())
        self._check_pattern(VentricularTachycardia())
        self._check_pattern(VentricularFibrillation())
        self._check_pattern(PulselessElectricalActivity())


class TestPriorityRhythmTiming(unittest.TestCase):
    def test_first_degree_av_block_uses_long_pr_interval(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        FirstDegreeAVBlock(
            heart_rate_bpm=60, duration_sec=1, pr_interval_ms=240
        ).apply_to_ecg(ecg)

        p_wave = _events_by_type(ecg, "PWave")[0]
        qrs = _events_by_type(ecg, "QRSComplex")[0]

        self.assertAlmostEqual(
            qrs["start_time"] - p_wave["start_time"], 0.24, places=3
        )

    def test_bundle_branch_block_uses_wide_qrs(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        BundleBranchBlock(
            heart_rate_bpm=60, duration_sec=1, qrs_duration_ms=140
        ).apply_to_ecg(ecg)

        qrs = _events_by_type(ecg, "QRSComplex")[0]

        self.assertEqual(qrs["segment"].duration_ms, 140)
        self.assertEqual(qrs["lead_profile"]["profile"], "rbbb")
        self.assertEqual(qrs["lead_profile"]["block_type"], "right")

    def test_wpw_uses_short_pr_and_delta_wave(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        WolffParkinsonWhite(
            heart_rate_bpm=60, duration_sec=1, pr_interval_ms=100
        ).apply_to_ecg(ecg)

        p_wave = _events_by_type(ecg, "PWave")[0]
        qrs = _events_by_type(ecg, "QRSComplex")[0]

        self.assertAlmostEqual(
            qrs["start_time"] - p_wave["start_time"], 0.10, places=3
        )
        self.assertGreater(qrs["segment"].delta_wave_duration_ms, 0)

    def test_svt_uses_narrow_qrs_without_visible_p_waves(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        SupraventricularTachycardia(
            heart_rate_bpm=180, duration_sec=1
        ).apply_to_ecg(ecg)

        self.assertEqual(_events_by_type(ecg, "PWave"), [])
        for qrs in _events_by_type(ecg, "QRSComplex"):
            self.assertLessEqual(qrs["segment"].duration_ms, 100)

    def test_asystole_flatlines_signal_and_events(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        Asystole().apply_to_ecg(ecg)

        self.assertEqual(ecg.segments_added, [])
        self.assertTrue((ecg.voltage == 0).all())

    def test_third_degree_av_block_dissociates_p_waves_and_qrs(self):
        ecg = ECGCore(duration_sec=4, sampling_rate=1000)
        ThirdDegreeAVBlock(
            atrial_rate_bpm=75, ventricular_rate_bpm=40
        ).apply_to_ecg(ecg)

        p_waves = _events_by_type(ecg, "PWave")
        qrs_events = _events_by_type(ecg, "QRSComplex")
        self.assertGreater(len(p_waves), len(qrs_events))
        self.assertGreater(len(qrs_events), 1)

        p_starts = [event["start_time"] for event in p_waves]
        qrs_offsets = []
        for qrs in qrs_events:
            preceding_p = max(
                start for start in p_starts if start <= qrs["start_time"]
            )
            qrs_offsets.append(round(qrs["start_time"] - preceding_p, 2))

        self.assertGreater(len(set(qrs_offsets)), 1)

    def test_mat_has_multiple_p_wave_morphologies_and_variable_pr(self):
        ecg = ECGCore(duration_sec=4, sampling_rate=1000)
        MultifocalAtrialTachycardia(
            heart_rate_bpm=120, duration_sec=4
        ).apply_to_ecg(ecg)

        p_waves = _events_by_type(ecg, "PWave")
        qrs_events = _events_by_type(ecg, "QRSComplex")
        p_shapes = {
            (event["segment"].duration_ms, event["segment"].amplitude_mv)
            for event in p_waves
        }
        pr_intervals = [
            round(qrs["start_time"] - p_waves[index]["start_time"], 2)
            for index, qrs in enumerate(qrs_events[:len(p_waves)])
        ]

        self.assertGreaterEqual(len(p_shapes), 3)
        self.assertGreater(len(set(pr_intervals)), 1)

    def test_ventricular_fibrillation_generates_chaotic_signal_without_events(self):
        ecg = ECGCore(duration_sec=2, sampling_rate=1000)
        RhythmVentricularFibrillation(rng_seed=1).apply_to_ecg(ecg)

        self.assertEqual(ecg.segments_added, [])
        self.assertGreater(np.max(ecg.voltage) - np.min(ecg.voltage), 0.1)

    def test_torsades_generates_wide_qrs_with_changing_polarity(self):
        ecg = ECGCore(duration_sec=3, sampling_rate=1000)
        TorsadesDePointes(
            ventricular_rate_bpm=200, twist_frequency_hz=0.5, duration_sec=3
        ).apply_to_ecg(ecg)

        qrs_events = _events_by_type(ecg, "QRSComplex")
        amplitudes = [event["segment"].r_amplitude_mv for event in qrs_events]

        self.assertGreater(len(qrs_events), 3)
        self.assertTrue(all(event["segment"].duration_ms >= 120 for event in qrs_events))
        self.assertGreater(max(amplitudes), 0)
        self.assertLess(min(amplitudes), 0)

    def test_torsades_twist_frequency_controls_amplitude_modulation(self):
        slow_ecg = ECGCore(duration_sec=3, sampling_rate=1000)
        fast_ecg = ECGCore(duration_sec=3, sampling_rate=1000)

        TorsadesDePointes(
            ventricular_rate_bpm=200, twist_frequency_hz=0.1, duration_sec=3
        ).apply_to_ecg(slow_ecg)
        TorsadesDePointes(
            ventricular_rate_bpm=200, twist_frequency_hz=0.5, duration_sec=3
        ).apply_to_ecg(fast_ecg)

        slow_amplitudes = [
            event["segment"].r_amplitude_mv
            for event in _events_by_type(slow_ecg, "QRSComplex")
        ]
        fast_amplitudes = [
            event["segment"].r_amplitude_mv
            for event in _events_by_type(fast_ecg, "QRSComplex")
        ]

        self.assertNotEqual(slow_amplitudes[:4], fast_amplitudes[:4])

    def test_cycle_helpers_use_current_segment_api(self):
        ecg = ECGCore(duration_sec=1, sampling_rate=1000)
        patterns = [
            BundleBranchBlock(duration_sec=1),
            SupraventricularTachycardia(duration_sec=1),
            WolffParkinsonWhite(duration_sec=1),
        ]

        for pattern in patterns:
            cycle = pattern._generate_cycle(ecg)
            self.assertGreater(len(cycle), 0)
            for segment, _ in cycle:
                _, voltage = segment.generate(ecg.sampling_rate)
                self.assertGreater(len(voltage), 0)

    def test_add_arrhythmia_pattern_accepts_lead_name_for_rhythm_overrides(self):
        patterns = [
            Asystole(),
            ThirdDegreeAVBlock(duration_sec=1),
            MultifocalAtrialTachycardia(duration_sec=1),
            RhythmVentricularFibrillation(rng_seed=1),
            TorsadesDePointes(duration_sec=1),
            VentricularTachycardia(duration_sec=1),
        ]

        for pattern in patterns:
            ecg = ECGCore(duration_sec=1, sampling_rate=1000)
            ecg.add_arrhythmia_pattern(pattern, lead_name="II")


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
