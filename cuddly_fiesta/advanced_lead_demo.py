"""Advanced multi-lead demonstration with per-lead waveform parameters."""

from pathlib import Path
import matplotlib.pyplot as plt

from .ecg_core import ECGCore
from .multi_lead import MultiLeadECG
from .waveform_segments import NormalSinusRhythm


def main() -> None:
    """Generate a multi-lead ECG using custom lead parameters."""
    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)

    lead_params = {
        "I": {"scale": 1.0},
        "II": {"scale": 1.1},
        "III": {"scale": 0.9},
        "aVR": {"scale": -0.8},
        "aVL": {"scale": 0.7},
        "aVF": {"scale": 1.0},
        "V1": {"scale": -0.6},
        "V2": {"scale": -0.4},
        "V3": {"scale": 0.3},
        "V4": {"scale": 0.8},
        "V5": {"scale": 1.2},
        "V6": {"scale": 1.3},
    }

    multi = MultiLeadECG(ecg, lead_params=lead_params)
    fig, _ = multi.plot_all_leads(with_grid=True)
    out_path = Path("advanced_multi_lead_demo.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Advanced multi-lead demo saved as '{out_path}'")


if __name__ == "__main__":
    main()
