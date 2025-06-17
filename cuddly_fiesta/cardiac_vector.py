"""Simple 3D cardiac vector model used as ground truth for electrical activity."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


class CardiacDipoleModel:
    """Time-varying 3D dipole representing the cardiac electrical vector."""

    def __init__(self, duration_sec: float = 1.0, sampling_rate: int = 1000) -> None:
        self.duration_sec = duration_sec
        self.sampling_rate = sampling_rate
        self.n_samples = int(duration_sec * sampling_rate)
        self.time = np.linspace(0, duration_sec, self.n_samples, endpoint=False)

    def generate_dipole(self) -> np.ndarray:
        """Return the dipole vector at each time step as an array of shape
        ``(n_samples, 3)``.
        """
        angle = 2 * np.pi * self.time / self.duration_sec
        amplitude = 1.0 + 0.2 * np.sin(2 * np.pi * self.time / self.duration_sec)
        dipole = np.stack(
            [
                amplitude * np.cos(angle),
                amplitude * np.sin(angle),
                0.1 * np.sin(2 * angle),
            ],
            axis=1,
        )
        return dipole

    def surface_potentials(
        self,
        electrode_positions: Iterable[Sequence[float]],
        conductivity: float = 0.2,
    ) -> np.ndarray:
        """Compute surface potentials for given electrode positions.

        Parameters
        ----------
        electrode_positions:
            Iterable of ``(x, y, z)`` electrode coordinates in centimeters.
        conductivity:
            Volume conductor conductivity in S/cm. A typical value is ``0.2``.
        """
        dipole = self.generate_dipole()
        potentials = []
        for pos in electrode_positions:
            r = np.asarray(pos, dtype=float)
            mag = np.linalg.norm(r)
            if mag == 0:
                raise ValueError("Electrode position cannot be at the dipole origin")
            pot = np.dot(dipole, r) / (4 * np.pi * conductivity * mag**3)
            potentials.append(pot)
        return np.asarray(potentials)

