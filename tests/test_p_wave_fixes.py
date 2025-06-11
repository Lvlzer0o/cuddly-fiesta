import unittest
import numpy as np
from cuddly_fiesta.p_wave_generator import PWaveGenerator


class TestPWaveGenerator(unittest.TestCase):
    def test_custom_parameters(self):
        """Custom duration and amplitude should be accepted."""
        PWaveGenerator(sampling_rate=1000, enable_noise=False,
                       target_duration_ms=100,
                       target_amplitude_mv=0.15)

    def test_default_parameters(self):
        """Default parameters instantiate correctly."""
        PWaveGenerator(sampling_rate=1000, enable_noise=False)

    def test_generate_p_wave_properties(self):
        """Generated P-wave matches target duration and amplitude."""
        gen = PWaveGenerator(sampling_rate=1000, enable_noise=False)
        data = gen.generate_p_wave(start_time_ms=0)
        duration_ms = (data['time'][-1] - data['time'][0]) * 1000
        amplitude_mv = np.max(data['voltage']) - np.min(data['voltage'])
        self.assertLessEqual(abs(duration_ms - gen.target_duration_ms), 40)
        self.assertAlmostEqual(amplitude_mv, gen.target_amplitude_mv, delta=0.05)

    def test_peak_location(self):
        """Peak of the waveform should occur around the middle."""
        gen = PWaveGenerator(sampling_rate=1000, enable_noise=False)
        data = gen.generate_p_wave(start_time_ms=0)
        peak_idx = np.argmax(data['voltage'])
        peak_fraction = peak_idx / len(data['voltage'])
        self.assertGreater(peak_fraction, 0.3)
        self.assertLess(peak_fraction, 0.7)


if __name__ == "__main__":
    unittest.main()
