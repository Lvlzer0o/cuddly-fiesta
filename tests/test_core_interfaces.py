import unittest

from cuddly_fiesta.core import GridScaling
from cuddly_fiesta.segments import PWave, QRSComplex


class TestWaveformParameterPreservation(unittest.TestCase):
    def test_pwave_preserves_clinical_defaults(self):
        wave = PWave()

        self.assertEqual(wave.duration_ms, 100)
        self.assertEqual(wave.amplitude_mv, 0.15)

    def test_qrs_preserves_clinical_defaults(self):
        qrs = QRSComplex()

        self.assertEqual(qrs.duration_ms, 100)
        self.assertEqual(qrs.r_amplitude_mv, 1.0)


class TestGridScaling(unittest.TestCase):
    def test_validate_timing_and_voltage(self):
        self.assertTrue(GridScaling.validate_timing(40))
        self.assertFalse(GridScaling.validate_timing(35))
        self.assertTrue(GridScaling.validate_voltage(0.1))
        self.assertFalse(GridScaling.validate_voltage(0.15))

class TestWaveformGenerate(unittest.TestCase):
    def test_pwave_generate_interface(self):
        t, v = PWave().generate(1000)
        self.assertEqual(len(t), len(v))
        self.assertGreater(len(t), 0)
        self.assertAlmostEqual(t[0], 0.0, places=5)

    def test_qrs_generate_interface(self):
        t, v = QRSComplex().generate(1000)
        self.assertEqual(len(t), len(v))
        self.assertGreater(len(t), 0)
        self.assertAlmostEqual(t[0], 0.0, places=5)

    def test_negative_qrs_amplitude_creates_dominant_negative_deflection(self):
        _, voltage = QRSComplex(r_amplitude_mv=-1.0).generate(1000)

        self.assertLess(voltage.min(), -0.8)
        self.assertGreater(abs(voltage.min()), voltage.max() * 2.0)

if __name__ == "__main__":
    unittest.main()
