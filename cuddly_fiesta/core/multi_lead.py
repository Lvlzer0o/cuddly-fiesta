"""Multi-lead ECG utilities."""

import csv
from typing import Dict, Iterable, Tuple, Optional
import matplotlib.pyplot as plt
import numpy as np

from .ecg_core import ECGCore


LEAD_ORDER = [
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


STANDARD_LEAD_PROFILE = {
    "I": 1.0,
    "II": 1.5,
    "III": 0.5,
    "aVR": -1.0,
    "aVL": 0.25,
    "aVF": 1.25,
    "V1": -5.0 / 6.0,
    "V2": -13.0 / 30.0,
    "V3": -7.0 / 30.0,
    "V4": 1.0 / 6.0,
    "V5": 7.0 / 15.0,
    "V6": 2.0 / 3.0,
}


COMPONENT_ALIASES = {
    "PWave": ("PWave", "P", "p_wave"),
    "QRSComplex": ("QRSComplex", "QRS", "qrs_complex"),
    "TWave": ("TWave", "T", "t_wave"),
    "UWave": ("UWave", "U", "u_wave"),
}


BUNDLE_BRANCH_BLOCK_TEMPLATE_LEADS = {
    "rbbb": {"V1", "V2", "I", "V5", "V6"},
    "lbbb": {"V1", "V2", "I", "aVL", "V5", "V6"},
}


class MultiLeadECG:
    """Generate a simple 12-lead ECG from an ``ECGCore`` instance."""

    def __init__(self, ecg: ECGCore, morphology: Optional[Dict] = None):
        self.ecg = ecg
        self.time = ecg.time
        if morphology is None:
            morphology = getattr(ecg, "lead_modifiers", {})
        self.lead_modifiers = morphology
        # Helper ECGCore instance used solely for drawing the grid.
        self._baseline_grid_helper: Optional[ECGCore] = None
        self._generate_leads()

    def _generate_leads(self) -> None:
        """Create all limb and precordial leads."""
        events = getattr(self.ecg, "events", getattr(self.ecg, "segments_added", []))
        if events:
            self.leads = self._synthesize_event_leads(events)
            return

        self.leads = self._project_scalar_voltage()

    def _project_scalar_voltage(self) -> Dict[str, np.ndarray]:
        """Fallback projection for ECGCore instances without event metadata."""
        base = self.ecg.voltage

        # Approximate limb potentials
        ra = -0.5 * base
        la = 0.5 * base
        ll = 1.0 * base

        leads: Dict[str, np.ndarray] = {
            "I": la - ra,
            "II": ll - ra,
            "III": ll - la,
            "aVR": ra - (la + ll) / 2,
            "aVL": la - (ra + ll) / 2,
            "aVF": ll - (ra + la) / 2,
        }

        # Wilson central terminal
        wct = (ra + la + ll) / 3

        chest_factors = [-0.5, -0.1, 0.1, 0.5, 0.8, 1.0]
        for i, factor in enumerate(chest_factors, start=1):
            leads[f"V{i}"] = factor * base - wct

        # Legacy whole-signal fallback for callers that supply raw voltage only.
        for name, signal in leads.items():
            leads[name] = self._apply_modifier(
                signal, self._flat_lead_modifier(name)
            )

        return leads

    def _synthesize_event_leads(
        self, events: Iterable[Dict[str, object]]
    ) -> Dict[str, np.ndarray]:
        leads = {
            name: np.zeros_like(self.time, dtype=float)
            for name in LEAD_ORDER
        }

        for event in events:
            segment = event["segment"]
            start = float(event["start_time"])
            component_type = str(
                event.get("component_type", segment.__class__.__name__)
            )
            seg_t, seg_v = segment.generate(self.ecg.sampling_rate)
            seg_t = seg_t + start
            valid = (seg_t < self.ecg.duration_sec) & (seg_t >= 0)
            if not np.any(valid):
                continue

            indices = np.clip(
                np.round(seg_t[valid] * self.ecg.sampling_rate).astype(int),
                0,
                len(self.time) - 1,
            )
            target_lead = event.get("lead")
            target_leads = [target_lead] if target_lead else LEAD_ORDER

            for lead_name in target_leads:
                if lead_name not in leads:
                    continue
                profile_scale = self._lead_profile_scale(lead_name, event)
                modifier = self._component_modifier(lead_name, component_type)
                lead_signal = self._lead_signal_for_event(
                    event, lead_name, seg_v[valid]
                )
                lead_signal = self._apply_modifier(lead_signal, modifier)
                np.add.at(leads[lead_name], indices, profile_scale * lead_signal)

        return leads

    @staticmethod
    def _lead_profile_scale(lead_name: str, event: Optional[Dict] = None) -> float:
        if event is not None:
            lead_profile = event.get("lead_profile", {})
            if (
                isinstance(lead_profile, dict)
                and lead_profile.get("profile") in ("rbbb", "lbbb")
                and lead_name in BUNDLE_BRANCH_BLOCK_TEMPLATE_LEADS[
                    lead_profile["profile"]
                ]
            ):
                return 1.0
        return STANDARD_LEAD_PROFILE.get(lead_name, 1.0)

    def _lead_signal_for_event(
        self,
        event: Dict[str, object],
        lead_name: str,
        default_signal: np.ndarray,
    ) -> np.ndarray:
        lead_profile = event.get("lead_profile", {})
        if not isinstance(lead_profile, dict):
            return default_signal

        profile = lead_profile.get("profile")
        component_type = event.get("component_type")
        if component_type != "QRSComplex" or profile not in ("rbbb", "lbbb"):
            return default_signal

        return self._bundle_branch_block_signal(
            str(profile), lead_name, default_signal
        )

    @staticmethod
    def _bundle_branch_block_signal(
        profile: str, lead_name: str, default_signal: np.ndarray
    ) -> np.ndarray:
        if default_signal.size == 0:
            return default_signal

        x = np.linspace(0.0, 1.0, default_signal.size, endpoint=False)
        amplitude = max(float(np.max(np.abs(default_signal))), 0.1)

        def narrow(center: float, width: float) -> np.ndarray:
            return np.exp(-0.5 * ((x - center) / width) ** 2)

        if profile == "rbbb":
            if lead_name in ("V1", "V2"):
                return amplitude * (
                    0.35 * narrow(0.28, 0.08)
                    + 1.15 * narrow(0.76, 0.10)
                )
            if lead_name in ("I", "V5", "V6"):
                return amplitude * (
                    0.8 * narrow(0.32, 0.10)
                    - 0.75 * narrow(0.76, 0.11)
                )
            return default_signal

        if lead_name in ("V1", "V2"):
            return -amplitude * (1.1 * narrow(0.52, 0.22))
        if lead_name in ("I", "aVL", "V5", "V6"):
            return amplitude * (
                1.05 * narrow(0.50, 0.20)
                + 0.45 * narrow(0.76, 0.16)
            )
        return default_signal

    def _component_modifier(
        self, lead_name: str, component_type: str
    ) -> Dict[str, float]:
        lead_mod = self.lead_modifiers.get(lead_name, {})
        modifier = self._flat_lead_modifier(lead_name)
        for key in COMPONENT_ALIASES.get(component_type, (component_type,)):
            component_mod = lead_mod.get(key)
            if component_mod:
                modifier.update(component_mod)
        return modifier

    def _flat_lead_modifier(self, lead_name: str) -> Dict[str, float]:
        lead_mod = self.lead_modifiers.get(lead_name, {})
        return {
            key: lead_mod[key]
            for key in ("scale", "polarity", "axis_deg", "offset")
            if key in lead_mod
        }

    @staticmethod
    def _apply_modifier(signal: np.ndarray, modifier: Dict[str, float]) -> np.ndarray:
        scale = modifier.get(
            "scale",
            modifier.get("r_scale", modifier.get("amplitude_scale", 1.0)),
        )
        polarity = modifier.get("polarity", 1.0)
        axis = np.cos(np.radians(modifier.get("axis_deg", 0.0)))
        offset = modifier.get("offset", 0.0)
        return scale * polarity * axis * signal + offset

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
        for ax, name in zip(axes.ravel(), LEAD_ORDER):
            ax.plot(self.time, self.leads[name], "k", linewidth=1)
            ax.set_title(name)
            ax.set_xlim(0, self.ecg.duration_sec)
            ax.set_ylim(-2, 2)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.axhline(0, color="gray", linewidth=0.5)
            if with_grid:
                # Reuse a single ECGCore instance for grid plotting
                if self._baseline_grid_helper is None:
                    self._baseline_grid_helper = ECGCore(
                        duration_sec=self.ecg.duration_sec,
                        sampling_rate=self.ecg.sampling_rate,
                    )
                plt.sca(ax)
                self._baseline_grid_helper._add_ecg_grid()

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
        with open(path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["time"] + LEAD_ORDER)
            for idx, t in enumerate(self.time):
                row = [t] + [self.leads[name][idx] for name in LEAD_ORDER]
                writer.writerow(row)

    @classmethod
    def from_ecg(cls, ecg: ECGCore, morphology: Optional[Dict] = None) -> "MultiLeadECG":
        """Create a ``MultiLeadECG`` from an existing ``ECGCore``."""
        return cls(ecg, morphology=morphology)


def main():
    """Example usage generating a 12-lead plot from a basic ECG."""
    import os
    from pathlib import Path

    from ..rhythms import NormalSinusRhythm

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
