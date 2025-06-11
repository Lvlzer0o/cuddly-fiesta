"""Command-line entry point for cuddly_fiesta.

This module allows running various parts of the cuddly_fiesta package
from the command line, such as generating baseline ECGs, animations,
launching the GUI, or running agent demos.

Use `python -m cuddly_fiesta --help` for usage details.
"""
import argparse
import matplotlib.pyplot as plt

from . import ecg_baseline, ecg_animation, ekg_ui, agents
from .ecg_core import ECGCore
from .multi_lead import MultiLeadECG
from .waveform_segments import NormalSinusRhythm


def _cmd_baseline(_args: argparse.Namespace) -> None:
    ecg_baseline.main(show_plot=True)


def _cmd_animate(args: argparse.Namespace) -> None:
    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)
    source = MultiLeadECG(ecg) if args.multi else ecg
    ecg_animation.animate_ecg(source, interval_ms=args.interval)
    plt.show()


def _cmd_gui(_args: argparse.Namespace) -> None:
    ekg_ui.main()


def _cmd_agent_run_all(_args: argparse.Namespace) -> None:
    agents.run_all()


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="cuddly_fiesta", description="ECG generator utilities")
    sub = parser.add_subparsers(dest="command", required=True)

    p_base = sub.add_parser("baseline", help="generate baseline plot")
    p_base.set_defaults(func=_cmd_baseline)

    p_anim = sub.add_parser("animate", help="run ECG animation")
    p_anim.add_argument("--multi", action="store_true", help="use 12-lead animation")
    p_anim.add_argument("--interval", type=int, default=40, help="animation interval ms")
    p_anim.set_defaults(func=_cmd_animate)

    p_gui = sub.add_parser("gui", help="launch Tk GUI")
    p_gui.set_defaults(func=_cmd_gui)

    p_agent = sub.add_parser("agent", help="agent utilities")
    agent_sub = p_agent.add_subparsers(dest="agent_cmd", required=True)
    p_run_all = agent_sub.add_parser("run-all", help="run full demo suite")
    p_run_all.set_defaults(func=_cmd_agent_run_all)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
