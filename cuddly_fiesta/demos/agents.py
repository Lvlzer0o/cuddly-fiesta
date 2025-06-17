"""Utility functions coordinating various demo modules.

This module exposes convenience helpers that exercise multiple pieces of the
``cuddly_fiesta`` package.  The functions provide simple entry points that are
useful for smoke testing or scripted demos.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..core import ClinicalValidator, ECGCore
from ..rhythms import NormalSinusRhythm
from ..tests.verify_improvements import main as verify_improvements_main

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_all() -> None:
    """Run a suite of demos and verifications."""
    logging.info("Running full demo suite")

    # Run health check
    health_check()

    # Run verification tests
    verify_improvements_main()

    logging.info("Demo suite complete")


def health_check() -> bool:
    """Perform a basic health check of core functionality."""
    logging.info("Starting health check")
    ok = True
    try:
        # Ensure ECGCore can be instantiated
        ecg = ECGCore(duration_sec=2, sampling_rate=1000)
        logging.info("ECGCore instantiated successfully.")

        # Validate that a simple rhythm can be created and applied
        pattern = NormalSinusRhythm(heart_rate_bpm=60)
        pattern.apply_to_ecg(ecg)
        logging.info("NormalSinusRhythm applied successfully.")

        # Also check the clinical validator
        ClinicalValidator()
        logging.info("ClinicalValidator instantiated successfully.")

    except Exception as exc:  # pragma: no cover - diagnostic path
        logging.warning(f"Health check failed: {exc}")
        ok = False

    if ok:
        logging.info("Health check passed")
        print("health-check passed")
    else:
        logging.warning("Health check reported issues")
        print("health-check failed")
    return ok


def report() -> None:
    """Generate and print a summary report of library status."""
    report_path = generate_report()
    print(report_path.read_text())


def generate_report(output_path: str = "agents_report.txt") -> Path:
    """Generate a short text report summarizing library status."""
    logging.info(f"Generating report at {output_path}")

    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)

    lines = [
        "ECG Generator Agents Report",
        "===========================",
        f"ECG Duration: {ecg.duration_sec} sec",
        f"Sampling rate: {ecg.sampling_rate} Hz",
        f"Segments added: {len(ecg.segments_added)}",
    ]

    out_path = Path(output_path)
    out_path.write_text("\n".join(lines))
    logging.info(f"Report written to {out_path}")
    return out_path

    return out_path
