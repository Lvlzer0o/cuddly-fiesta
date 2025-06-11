"""Utility functions used by the command line interface."""

from . import verify_improvements
from . import p_wave_generator
from . import waveform_segments
from .clinical_validator import ClinicalValidator
from .p_wave_summary import print_p_wave_summary


def run_all() -> None:
    """Run all demonstration and verification routines."""
    verify_improvements.main()
    p_wave_generator.main()
    waveform_segments.main()


def health_check() -> bool:
    """Simple health check ensuring the validator instantiates."""
    try:
        ClinicalValidator()
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"health-check failed: {exc}")
        return False
    print("health-check passed")
    return True


def report() -> None:
    """Print a summary report of the P-wave implementation."""
    print_p_wave_summary()
