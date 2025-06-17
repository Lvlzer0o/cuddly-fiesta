"""Command-line interface for the ECG Generator.

This package contains all CLI-related functionality for the ECG Generator,
including command definitions, argument parsing, and command handlers.
"""

# Export the main click command group
from .main import cli

__all__ = ['cli']
