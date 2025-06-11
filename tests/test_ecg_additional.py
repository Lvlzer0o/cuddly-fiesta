import unittest
import numpy as np

from waveform_segments import TWave, UWave, NormalSinusRhythm
from ecg_core import ECGCore
from multi_lead import MultiLeadECG, animate_ecg

class TestWaveformSegments(unittest.TestCase):
    def test_twave_properties(self):
        tw = TWave(amplitude_mv=0.3, duration_ms=160)
        time, voltage = tw.generate(sampling_rate=1000)
        self.assertEqual(len(time), 160)
        self.assertTrue(tw.grid.validate_timing(tw.duration_ms))
        self.assertTrue(tw.grid.validate_amplitude(tw.amplitude_mv))
        self.assertAlmostEqual(np.max(voltage), 0.3, delta=0.05)

    def test_uwave_properties(self):
        uw = UWave(amplitude_mv=0.1, duration_ms=80)
        time, voltage = uw.generate(sampling_rate=1000)
        self.assertEqual(len(time), 80)
        self.assertTrue(uw.grid.validate_timing(uw.duration_ms))
        self.assertTrue(uw.grid.validate_amplitude(uw.amplitude_mv))
        self.assertAlmostEqual(np.max(voltage), 0.1, delta=0.02)

class TestArrhythmiaPattern(unittest.TestCase):
    def test_normal_sinus_rhythm_application(self):
        ecg = ECGCore(duration_sec=2, sampling_rate=1000)
        nsr = NormalSinusRhythm(heart_rate_bpm=70)
        nsr.apply_to_ecg(ecg)
        self.assertEqual(len(ecg.segments_added), 3)
        for seg in ecg.segments_added:
            self.assertTrue(seg['segment'].grid.validate_timing(seg['segment'].duration_ms))

class TestMultiLead(unittest.TestCase):
    def test_multilead_generation(self):
        ml = MultiLeadECG(duration_sec=1, sampling_rate=200)
        time, leads = ml.generate_leads()
        self.assertEqual(leads.shape[0], 12)
        self.assertEqual(leads.shape[1], len(time))

    def test_animate_ecg_smoke(self):
        ml = MultiLeadECG(duration_sec=1, sampling_rate=50)
        time, leads = ml.generate_leads()
        ani = animate_ecg(time, leads[0])
        self.assertIsNotNone(ani)

if __name__ == "__main__":
    unittest.main()
