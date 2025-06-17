"""Access the :mod:`run` module shipped with the repository."""

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
run = importlib.import_module("run")

ClinicalValidator = run.ClinicalValidator

__all__ = ["ClinicalValidator"]
