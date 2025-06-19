import unittest

from cuddly_fiesta.core import GridScaling
from cuddly_fiesta.segments import PWave, QRSComplex

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

if __name__ == "__main__":
    unittest.main()
