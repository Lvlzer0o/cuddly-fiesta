#!/usr/bin/env python
"""
Interactive ECG Visualizer

This script launches an interactive ECG visualization tool with controls for
selecting different rhythms and adjusting parameters in real-time.
"""

def main():
    """Launch the ECG visualizer application."""
    from cuddly_fiesta import run_visualizer
    run_visualizer()

if __name__ == "__main__":
    main()
