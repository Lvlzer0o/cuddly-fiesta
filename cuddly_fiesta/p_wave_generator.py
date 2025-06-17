import numpy as np


class PWaveGenerator:
    """Very small P-wave generator used for tests."""

    def __init__(
        self,
        sampling_rate: int = 1000,
        enable_noise: bool = True,
        target_duration_ms: float = 100,
        target_amplitude_mv: float = 0.15,
    ) -> None:
        self.sampling_rate = sampling_rate
        self.enable_noise = enable_noise
        self.target_duration_ms = target_duration_ms
        self.target_amplitude_mv = target_amplitude_mv

    def generate_p_wave(self, start_time_ms: float = 0) -> dict:
        n = int(self.target_duration_ms * self.sampling_rate / 1000)
        t0 = start_time_ms / 1000
        time = np.linspace(t0, t0 + self.target_duration_ms / 1000, n, endpoint=False)
        x = np.linspace(-1, 1, n)
        voltage = self.target_amplitude_mv * np.exp(-5 * x**2)
        if self.enable_noise:
            voltage += np.random.normal(0, 0.01, n)
        return {"time": time, "voltage": voltage}

__all__ = ["PWaveGenerator"]
