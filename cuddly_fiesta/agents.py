"""Utility functions coordinating various demo modules.

This module exposes convenience helpers that exercise multiple pieces of the
``cuddly_fiesta`` package.  The functions provide simple entry points that are
useful for smoke testing or scripted demos.
"""

from __future__ import annotations

import logging
from pathlib import Path

from . import ecg_baseline
from . import p_wave_generator
from . import waveform_segments
from .ecg_core import ECGCore
from .waveform_segments import NormalSinusRhythm
from .clinical_validator import ClinicalValidator
from .p_wave_summary import print_p_wave_summary
from .verify_improvements import main as verify_improvements_main

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def run_all() -> None:
    """Run a suite of demos and verifications.

    This function executes several of the example routines shipped with the
    project.  Generated plots are written to the current ``OUTPUT_DIR`` (see the
    individual modules for details).
    """
    logging.info("Running full demo suite")

    # Baseline generation
    ecg_baseline.main(show_plot=False)

    # Demonstrate waveform segment modules
    waveform_segments.demo_modular_segments()
    waveform_segments.demo_arrhythmia_pattern_swap()
    
    # Run additional demo modules
    p_wave_generator.main()
    waveform_segments.main()

    # Clinical verification and summaries
    verify_improvements_main()
    print_p_wave_summary()

    logging.info("Demo suite complete")


def health_check() -> bool:
    """Perform a basic health check of core functionality."""
    logging.info("Starting health check")

    # Ensure baseline can be generated
    baseline = ecg_baseline.ECGBaseline(duration_sec=1, sampling_rate=1000)
    data = baseline.get_baseline_data()
    logging.info("Baseline generated with %d samples", len(data["time"]))

    # Validate that a simple rhythm can be created and checked
    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    pattern = NormalSinusRhythm(heart_rate_bpm=60)
    pattern.apply_to_ecg(ecg)
    ok = ecg.validate_grid_integrity()
    
    # Also check the clinical validator
    try:
        ClinicalValidator()
    except Exception as exc:  # pragma: no cover - diagnostic path
        logging.warning("Clinical validator check failed: %s", exc)
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
    print_p_wave_summary()
    

def generate_report(output_path: str = "agents_report.txt") -> Path:
    """Generate a short text report summarizing library status."""
    logging.info("Generating report at %s", output_path)

    baseline = ecg_baseline.ECGBaseline(duration_sec=1, sampling_rate=1000)
    bdata = baseline.get_baseline_data()

    ecg = ECGCore(duration_sec=2, sampling_rate=1000)
    NormalSinusRhythm(heart_rate_bpm=70).apply_to_ecg(ecg)

    lines = [
        "ECG Generator Agents Report",
        "===========================",
        f"Baseline duration: {bdata['duration_sec']} sec",
        f"Sampling rate: {bdata['sampling_rate']} Hz",
        f"Segments added: {len(ecg.segments_added)}",
    ]

    out_path = Path(output_path)
    out_path.write_text("\n".join(lines))
    logging.info("Report written to %s", out_path)
    return out_path
