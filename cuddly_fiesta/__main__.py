"""Command-line entry point for cuddly_fiesta.

This module allows running various parts of the cuddly_fiesta package
from the command line, such as generating baseline ECGs, animations,
launching the GUI, or running agent demos.

Use `python -m cuddly_fiesta --help` for usage details.
"""

import argparse
from typing import List, Optional

import matplotlib.pyplot as plt

from . import agents, ecg_baseline, ekg_ui
from .ecg_animation import animate_ecg
from .ecg_core import ECGCore
from .multi_lead import MultiLeadECG
from .waveform_segments import NormalSinusRhythm, demo_afib, demo_normal


def _cmd_baseline(_args: argparse.Namespace) -> None:
    """Handles the 'baseline' subcommand.

    Generates and displays a baseline ECG plot by calling `ecg_baseline.main()`.
    The `_args` parameter is currently unused by this specific command.
    """
    ecg_baseline.main(show_plot=True)


def _cmd_animate(args: argparse.Namespace) -> None:
    """Handles the 'animate' subcommand.

    Creates an ECG animation with optional multi-lead display.
    """
    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)
    source = MultiLeadECG(ecg) if args.multi else ecg
    animate_ecg(source, interval_ms=args.interval, show_grid=args.grid)
    plt.show()


def _cmd_gui(_args: argparse.Namespace) -> None:
    """Handles the 'gui' subcommand.

    Launches the Tk-based GUI interface.
    """
    ekg_ui.main()


def _cmd_demo_normal(_args: argparse.Namespace) -> None:
    """Handles the 'demo normal' subcommand."""
    demo_normal()


def _cmd_demo_afib(_args: argparse.Namespace) -> None:
    """Handles the 'demo afib' subcommand."""
    demo_afib()


def _cmd_agent_run_all(_args: argparse.Namespace) -> None:
    """Handles the 'agent run-all' subcommand."""
    agents.run_all()


def _cmd_agent_health_check(_args: argparse.Namespace) -> None:
    """Handles the 'agent health-check' subcommand."""
    agents.health_check()


def _cmd_agent_report(_args: argparse.Namespace) -> None:
    """Handles the 'agent report' subcommand."""
    agents.report()


def main(argv: Optional[List[str]] = None) -> None:
    """Main entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="cuddly_fiesta", description="ECG generator utilities"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Baseline command
    p_base = sub.add_parser("baseline", help="generate baseline plot")
    p_base.set_defaults(func=_cmd_baseline)

    # Demo commands
    p_demo = sub.add_parser("demo", help="run demonstration examples")
    demo_sub = p_demo.add_subparsers(dest="demo_cmd", required=True)
    p_normal = demo_sub.add_parser("normal", help="normal sinus rhythm demo")
    p_normal.set_defaults(func=_cmd_demo_normal)
    p_afib = demo_sub.add_parser("afib", help="atrial fibrillation demo")
    p_afib.set_defaults(func=_cmd_demo_afib)

    # Animation command
    p_anim = sub.add_parser("animate", help="run ECG animation")
    p_anim.add_argument(
        "--multi", action="store_true", help="use 12-lead animation"
    )
    p_anim.add_argument(
        "--interval", type=int, default=40, help="animation interval ms"
    )
    p_anim.add_argument(
        "--grid",
        action="store_true",
        help="overlay ECG grid on the animation",
    )
    p_anim.set_defaults(func=_cmd_animate)

    # GUI command
    p_gui = sub.add_parser("gui", help="launch Tk GUI")
    p_gui.set_defaults(func=_cmd_gui)

    # Agent commands
    p_agent = sub.add_parser("agent", help="agent utilities")
    agent_sub = p_agent.add_subparsers(dest="agent_cmd", required=True)

    p_run_all = agent_sub.add_parser("run-all", help="run full demo suite")
    p_run_all.set_defaults(func=_cmd_agent_run_all)

    p_health = agent_sub.add_parser(
        "health-check", help="run system health check"
    )
    p_health.set_defaults(func=_cmd_agent_health_check)

    p_report = agent_sub.add_parser("report", help="generate agent report")
    p_report.set_defaults(func=_cmd_agent_report)

    # Parse and dispatch
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
