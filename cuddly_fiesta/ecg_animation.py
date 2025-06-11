"""ECG animation utilities using matplotlib."""

from typing import Union, Optional
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .ecg_core import ECGCore
from .multi_lead import MultiLeadECG


def _animate_single_lead(ecg: ECGCore, interval_ms: int) -> FuncAnimation:
    """Animate a single-lead ECG."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, ecg.duration_sec)
    ax.set_ylim(-2, 2)
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Voltage (mV)")
    ax.set_title("ECG Animation")
    ax.axhline(0, color="gray", linewidth=0.5)

    line, = ax.plot([], [], "k", linewidth=1)
    time = ecg.time
    voltage = ecg.voltage

    def init():
        line.set_data([], [])
        return (line,)

    def update(frame):
        line.set_data(time[:frame], voltage[:frame])
        return (line,)

    return FuncAnimation(
        fig,
        update,
        frames=len(time),
        init_func=init,
        interval=interval_ms,
        blit=True,
    )


def _animate_multi_lead(multi: MultiLeadECG, interval_ms: int) -> FuncAnimation:
    """Animate all 12 leads in a 4x3 grid."""
    order = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    fig, axes = plt.subplots(4, 3, figsize=(12, 8), sharex=True, sharey=True)
    lines = []
    for ax, name in zip(axes.ravel(), order):
        ax.set_xlim(0, multi.ecg.duration_sec)
        ax.set_ylim(-2, 2)
        ax.set_title(name)
        ax.axhline(0, color="gray", linewidth=0.5)
        ax.set_xticks([])
        ax.set_yticks([])
        line, = ax.plot([], [], "k", linewidth=1)
        lines.append(line)

    time = multi.time
    leads = [multi.leads[name] for name in order]

    def init():
        for ln in lines:
            ln.set_data([], [])
        return lines

    def update(frame):
        for ln, data in zip(lines, leads):
            ln.set_data(time[:frame], data[:frame])
        return lines

    fig.suptitle("Real-time 12-Lead ECG", fontsize=14, fontweight="bold")
    plt.tight_layout()

    return FuncAnimation(
        fig,
        update,
        frames=len(time),
        init_func=init,
        interval=interval_ms,
        blit=True,
    )


def animate_ecg(ecg_source: Union[ECGCore, MultiLeadECG], interval_ms: int = 40) -> FuncAnimation:
    """Animate ECG data from ``ECGCore`` or ``MultiLeadECG``."""
    if isinstance(ecg_source, MultiLeadECG):
        return _animate_multi_lead(ecg_source, interval_ms)
    elif isinstance(ecg_source, ECGCore):
        return _animate_single_lead(ecg_source, interval_ms)
    else:
        raise TypeError("ecg_source must be ECGCore or MultiLeadECG")


ani: Optional[FuncAnimation] = None


def main() -> Optional[FuncAnimation]:
    """Load example segments and display a real-time animation."""
    import argparse
    from .waveform_segments import NormalSinusRhythm

    parser = argparse.ArgumentParser(description="Real-time ECG animation demo")
    parser.add_argument(
        "--multi",
        action="store_true",
        help="animate a 12-lead display",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=40,
        help="animation interval in milliseconds",
    )
    args = parser.parse_args()

    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    pattern = NormalSinusRhythm(heart_rate_bpm=70)
    pattern.apply_to_ecg(ecg)

    global ani
    source = MultiLeadECG(ecg) if args.multi else ecg
    ani = animate_ecg(source, interval_ms=args.interval)
    plt.show()
    return ani


if __name__ == "__main__":
    main()
