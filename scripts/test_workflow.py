#!/usr/bin/env python3
"""Run non-Godot tests for the operational workflow validator."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
suite = unittest.defaultTestLoader.discover(
    str(ROOT / "tests" / "operational"), pattern="test_*.py"
)
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
