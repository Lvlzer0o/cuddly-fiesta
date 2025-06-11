import argparse
import matplotlib.pyplot as plt

from . import ecg_baseline
from . import ecg_animation
from . import ekg_ui
from . import agents
from .ecg_core import ECGCore
from .multi_lead import MultiLeadECG
from .ecg_animation import animate_ecg
from .waveform_segments import (
    NormalSinusRhythm,
    demo_normal,
    demo_afib,
)


def _run_animation(multi: bool) -> None:
    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    NormalSinusRhythm().apply_to_ecg(ecg)
    source = MultiLeadECG(ecg) if multi else ecg
    animate_ecg(source)
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="cuddly-fiesta utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("baseline")

    demo_parser = subparsers.add_parser("demo")
    demo_sub = demo_parser.add_subparsers(dest="demo_cmd", required=True)
    demo_sub.add_parser("normal")
    demo_sub.add_parser("afib")

    anim = subparsers.add_parser("animate")
    anim.add_argument("--multi", action="store_true")

    subparsers.add_parser("gui")

    agent = subparsers.add_parser("agent")
    agent_sub = agent.add_subparsers(dest="agent_cmd", required=True)
    agent_sub.add_parser("run-all")
    agent_sub.add_parser("health-check")
    agent_sub.add_parser("report")

    args = parser.parse_args()

    if args.command == "baseline":
        ecg_baseline.main()
    elif args.command == "demo":
        if args.demo_cmd == "normal":
            demo_normal()
        elif args.demo_cmd == "afib":
            demo_afib()
    elif args.command == "animate":
        _run_animation(args.multi)
    elif args.command == "gui":
        ekg_ui.main()
    elif args.command == "agent":
        if args.agent_cmd == "run-all":
            agents.run_all()
        elif args.agent_cmd == "health-check":
            agents.health_check()
        elif args.agent_cmd == "report":
            agents.report()


if __name__ == "__main__":
    main()
