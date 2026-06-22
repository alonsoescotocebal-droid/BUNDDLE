"""Run unittest discovery behind ``python -m pytest``."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


def main() -> int:
    verbosity = 1 if "-q" in sys.argv else 2
    top_level = str(Path.cwd())
    suite = unittest.defaultTestLoader.discover("tests", top_level_dir=top_level)
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
