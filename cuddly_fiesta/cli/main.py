"""Main CLI module for the ECG Generator.

This module defines the main CLI command group and top-level commands.
"""

import click
from typing import Optional

# Create the main command group
@click.group()
@click.version_option()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """ECG Generator - A tool for generating realistic ECG signals."""
    # Ensure context.obj exists and is a dict
    ctx.ensure_object(dict)
    
    # Store global options
    ctx.obj['VERBOSE'] = verbose
    
    if verbose:
        click.echo("Verbose mode enabled")

# Import subcommands to register them with the CLI
# These imports must be after the cli group is defined to avoid circular imports
from . import (  # noqa: E402
    rhythm_commands,
    # Add other command modules here as they are implemented
)

# This allows the module to be run directly for testing
if __name__ == '__main__':
    cli(obj={})
