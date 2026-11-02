"""Fetch the calibration positives (read-only GitHub REST) and print the ids."""
import json
from pathlib import Path

from typediff.calibration import fetch_positives

dest = Path("calibration/positives.json")
cases = fetch_positives(dest)
print(len(cases), "cases ->", dest)
print(" ".join(sorted(c["id"] for c in cases)))
