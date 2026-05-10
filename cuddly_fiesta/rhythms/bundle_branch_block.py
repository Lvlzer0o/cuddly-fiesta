"""Implementation of the Bundle-Branch Block arrhythmia pattern."""

from __future__ import annotations

from ..core import ECGCore
from ..segments import PWave, QRSComplex, TWave
from .normal_sinus import NormalSinusRhythm


class BundleBranchBlock(NormalSinusRhythm):
    """Represents the Bundle-Branch Block arrhythmia pattern."""

    def __init__(
        self,
        qrs_duration_ms: float = 140.0,
        block_type: str = "right",
        **kwargs,
    ):
        """
        Initializes the Bundle-Branch Block pattern.

        Args:
            qrs_duration_ms: The duration of the QRS complex in milliseconds (typically > 120ms).
            block_type: Bundle branch side, either "right"/"rbbb" or "left"/"lbbb".
        """
        super().__init__(**kwargs)
        if qrs_duration_ms <= 120:
            raise ValueError("Bundle-Branch Block requires a QRS duration > 120ms.")
        block_type = block_type.lower()
        if block_type in ("right", "rbbb"):
            block_type = "right"
        elif block_type in ("left", "lbbb"):
            block_type = "left"
        else:
            raise ValueError("Bundle-Branch Block type must be 'right' or 'left'.")
        self.qrs_duration_ms = qrs_duration_ms
        self.block_type = block_type

    @property
    def _lead_profile_name(self) -> str:
        return "rbbb" if self.block_type == "right" else "lbbb"

    def _generate_cycle(self, ecg: ECGCore) -> list[tuple[PWave | QRSComplex | TWave, float]]:
        """Generates a single ECG cycle with a widened QRS complex."""
        p_wave = PWave(amplitude_mv=0.15, duration_ms=100)

        # Create a widened QRS complex
        qrs_complex = QRSComplex(
            duration_ms=self.qrs_duration_ms,
            q_duration_ms=self.qrs_duration_ms * 0.2,  # Proportional scaling
            r_duration_ms=self.qrs_duration_ms * 0.6,
            s_duration_ms=self.qrs_duration_ms * 0.2,
        )
        qrs_complex.event_metadata = {
            "lead_profile": {
                "profile": self._lead_profile_name,
                "block_type": self.block_type,
            }
        }

        t_wave = TWave(amplitude_mv=-0.25, duration_ms=160)

        # Timing calculations
        pr_interval_sec = 0.16
        qrs_duration_sec = qrs_complex.duration_ms / 1000.0
        st_segment_sec = 0.120  # 120ms
        t_wave_start_time = pr_interval_sec + qrs_duration_sec + st_segment_sec

        return [
            (p_wave, 0),
            (qrs_complex, pr_interval_sec),
            (t_wave, t_wave_start_time),
        ]

    def define_pattern(self) -> None:
        """Define sinus beats with widened bundle-branch-block QRS complexes."""
        self.segments = []
        current_time = 0.0

        while current_time < self.duration_sec:
            p_wave = PWave(amplitude_mv=0.15, duration_ms=100)
            qrs = QRSComplex(duration_ms=self.qrs_duration_ms)
            qrs.event_metadata = {
                "lead_profile": {
                    "profile": self._lead_profile_name,
                    "block_type": self.block_type,
                }
            }
            t_wave = TWave(amplitude_mv=-0.25, duration_ms=160)

            self.add_segment(current_time, p_wave)
            self.add_segment(current_time + 0.16, qrs)
            self.add_segment(
                current_time + 0.16 + self.qrs_duration_ms / 1000.0 + 0.08,
                t_wave,
            )

            current_time += self.rr_interval_sec
