"""QRS complex segment for ECG waveforms."""

import numpy as np
from scipy.signal import gaussian
from .base import WaveformSegment


class QRSComplex(WaveformSegment):
    """QRS complex segment representing ventricular depolarization.
    
    Generates a sharp triphasic waveform (Q, R, S) with adjustable
    component ratios and clinically validated timing.
    """
    
    def __init__(
        self,
        duration_ms: float = 100,
        q_duration_ms: float = 20.0,
        r_duration_ms: float = 60.0,
        s_duration_ms: float = 40.0,
        q_amplitude_mv: float = -0.2,
        r_amplitude_mv: float = 1.0,
        s_amplitude_mv: float = -0.4,
        delta_wave_duration_ms: float = 0.0,
    ) -> None:
        """Initialize QRS complex segment.
        
        Args:
            duration_ms: Total duration in milliseconds (80-200 ms)
            q_duration_ms: Duration of the Q wave in ms.
            r_duration_ms: Duration of the R wave in ms.
            s_duration_ms: Duration of the S wave in ms.
            q_amplitude_mv: Amplitude of the Q wave in mV.
            r_amplitude_mv: Amplitude of the R wave in mV.
            s_amplitude_mv: Amplitude of the S wave in mV.
            delta_wave_duration_ms: Duration of the delta wave in ms.
            
        Raises:
            ValueError: If parameters are outside clinical ranges
        """
        if not (80 <= duration_ms <= 200):
            raise ValueError(
                f"QRS duration {duration_ms}ms outside clinical range (80-200ms)"
            )

        if not (0.5 <= r_amplitude_mv <= 3.0):
            raise ValueError(
                f"R amplitude {r_amplitude_mv}mV outside clinical range (0.5-3.0mV)"
            )

        if not (0.1 <= q_amplitude_mv / r_amplitude_mv <= 0.3):
            raise ValueError(f"Q ratio {q_amplitude_mv / r_amplitude_mv} outside range (0.1-0.3)")
            
        if not (0.2 <= s_amplitude_mv / r_amplitude_mv <= 0.4):
            raise ValueError(f"S ratio {s_amplitude_mv / r_amplitude_mv} outside range (0.2-0.4)")

        super().__init__(duration_ms, r_amplitude_mv)
        self.q_duration_ms = q_duration_ms
        self.r_duration_ms = r_duration_ms
        self.s_duration_ms = s_duration_ms
        self.q_amplitude_mv = q_amplitude_mv
        self.r_amplitude_mv = r_amplitude_mv
        self.s_amplitude_mv = s_amplitude_mv
        self.delta_wave_duration_ms = delta_wave_duration_ms
    
    def generate(self, sampling_rate: int) -> np.ndarray:
        """Generate QRS complex using triple-component model.
        
        Args:
            sampling_rate: Sampling rate in Hz
            
        Returns:
            QRS complex voltage values
        """
        # Time array in seconds
        t = np.linspace(0, self.duration_ms / 1000, 
                       int(self.duration_ms * sampling_rate / 1000),
                       endpoint=False)
        
        # Create Q, R, S components
        qrs = np.zeros_like(t)
        
        # Q wave (negative deflection)
        q_wave_len = self._ms_to_samples(self.q_duration_ms)
        q_wave = self._generate_wave(q_wave_len, self.q_amplitude_mv, wave_type="gaussian")
        q_start = int(0.1 * len(t))
        end = min(q_start + len(q_wave), len(qrs))
        qrs[q_start:end] = q_wave[:end-q_start]
        
        # R wave (main positive deflection)
        r_wave_len = self._ms_to_samples(self.r_duration_ms)
        r_wave = self._generate_wave(r_wave_len, self.r_amplitude_mv, wave_type="gaussian")
        
        # Add delta wave if present (slurred upstroke of R wave)
        if self.delta_wave_duration_ms > 0:
            delta_len = self._ms_to_samples(self.delta_wave_duration_ms)
            if delta_len > 0:
                # Create a slow ramp for the delta wave
                delta_wave = np.linspace(0, self.r_amplitude_mv * 0.5, delta_len)
                # Prepend it to the R wave and shorten the R wave accordingly
                if len(r_wave) > delta_len:
                    r_wave = r_wave[delta_len:]
                    r_wave = np.concatenate([delta_wave, r_wave])

        r_start = int(0.3 * len(t))
        end = min(r_start + len(r_wave), len(qrs))
        qrs[r_start:end] = np.maximum(qrs[r_start:end], r_wave[:end-r_start])
        
        # S wave (negative after R)
        s_wave_len = self._ms_to_samples(self.s_duration_ms)
        s_wave = self._generate_wave(s_wave_len, self.s_amplitude_mv, wave_type="gaussian")
        s_start = int(0.6 * len(t))
        end = min(s_start + len(s), len(qrs))
        qrs[s_start:end] = np.minimum(qrs[s_start:end], s[:end-s_start])
        
        return qrs.astype(np.float32)
