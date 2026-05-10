#!/usr/bin/env python
"""Legacy launcher for the canonical ECG visualizer."""

from cuddly_fiesta import run_visualizer


def main() -> None:
    """Launch the public ECG visualizer."""
    run_visualizer()


if __name__ == "__main__":
    main()
