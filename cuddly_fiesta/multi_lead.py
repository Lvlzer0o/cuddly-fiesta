"""Multi-lead ECG utilities."""

import csv
from typing import Dict, Tuple, Optional

import matplotlib.pyplot as plt
import numpy as np

from .ecg_baseline import ECGBaseline
from .ecg_core import ECGCore


class MultiLeadECG:
    """Generate a simple 12-lead ECG from an ``ECGCore`` instance."""

    def __init__(self, ecg: ECGCore):
        self.ecg = ecg
        self.time = ecg.time
        # Helper for drawing the grid when plotting. Lazily initialised.
        self._baseline_grid_helper: Optional[ECGBaseline] = None
        self._generate_leads()

    def _generate_leads(self) -> None:
        """Create all limb and precordial leads."""
        base = self.ecg.voltage
        modifiers = getattr(self.ecg, "lead_modifiers", {})

        # Approximate limb potentials
        ra = -0.5 * base
        la = 0.5 * base
        ll = 1.0 * base

        leads: Dict[str, Tuple] = {}
        leads["I"] = la - ra
        leads["II"] = ll - ra
        leads["III"] = ll - la

        # Augmented limb leads
        leads["aVR"] = ra - (la + ll) / 2
        leads["aVL"] = la - (ra + ll) / 2
        leads["aVF"] = ll - (ra + la) / 2

        # Wilson central terminal
        wct = (ra + la + ll) / 3

        chest_factors = [-0.5, -0.1, 0.1, 0.5, 0.8, 1.0]
        for i, factor in enumerate(chest_factors, start=1):
            leads[f"V{i}"] = factor * base - wct

        # Apply lead-specific modifiers
        for name, signal in leads.items():
            mod = modifiers.get(name, {})
            scale = mod.get("scale", 1.0)
            polarity = mod.get("polarity", 1.0)
            axis = np.cos(np.radians(mod.get("axis_deg", 0.0)))
            leads[name] = scale * polarity * axis * signal

        self.leads = leads

    def get_lead(self, name: str):
        """Return the voltage array for the specified lead."""
        return self.leads[name]

    def plot_all_leads(
        self, figure_size: Tuple[int, int] = (12, 8), with_grid: bool = False
    ):
        """Plot all 12 leads in a 4x3 grid.

        Parameters
        ----------
        figure_size : tuple
            Size of the figure.
        with_grid : bool
            If ``True`` overlay a clinical ECG grid on each subplot.
        """
        fig, axes = plt.subplots(
            4, 3, figsize=figure_size, sharex=True, sharey=True
        )
        order = [
            "I",
            "II",
            "III",
            "aVR",
            "aVL",
            "aVF",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
        ]

        for ax, name in zip(axes.ravel(), order):
            ax.plot(self.time, self.leads[name], "k", linewidth=1)
            ax.set_title(name)
            ax.set_xlim(0, self.ecg.duration_sec)
            ax.set_ylim(-2, 2)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axhline(0, color="gray", linewidth=0.5)
            if with_grid:
                # Reuse a single ECGBaseline instance for grid plotting
                if self._baseline_grid_helper is None:
                    self._baseline_grid_helper = ECGBaseline(
                        self.ecg.duration_sec, self.ecg.sampling_rate
                    )
                self._baseline_grid_helper._add_ecg_grid(ax)

        fig.suptitle("12-Lead ECG", fontsize=14, fontweight="bold")
        plt.tight_layout()
        return fig, axes

    def save_plot(
        self,
        path: str,
        figure_size: Tuple[int, int] = (12, 8),
        with_grid: bool = False,
    ) -> None:
        """Save the multi-lead plot to ``path``."""
        fig, _ = self.plot_all_leads(
            figure_size=figure_size, with_grid=with_grid
        )
        plt.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)

    def export_to_csv(self, path: str) -> None:
        """Export all leads to a CSV file for analysis."""
        order = [
            "I",
            "II",
            "III",
            "aVR",
            "aVL",
            "aVF",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
        ]
        with open(path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["time"] + order)
            for idx, t in enumerate(self.time):
                row = [t] + [self.leads[name][idx] for name in order]
                writer.writerow(row)


def main():
    """Example usage generating a 12-lead plot from a basic ECG."""
    import os
    from pathlib import Path

    from .waveform_segments import NormalSinusRhythm

    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    pattern = NormalSinusRhythm(heart_rate_bpm=70)
    pattern.apply_to_ecg(ecg)

    ml = MultiLeadECG(ecg)
    fig, _ = ml.plot_all_leads()

    out_dir = Path(os.getenv("OUTPUT_DIR", "."))
    out_path = out_dir / "multi_lead_demo.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Multi-lead demo saved as '{out_path}'")


if __name__ == "__main__":
    main()
