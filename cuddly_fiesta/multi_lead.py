import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
run = importlib.import_module("run")

MultiLeadECG = run.MultiLeadECG

__all__ = ["MultiLeadECG"]
