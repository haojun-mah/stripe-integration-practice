"""Run staged acceptance checks. No manually running server is required."""

import argparse
from pathlib import Path
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("setup", "1", "2", "all"), default="all")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    pattern = {"setup": "test_setup.py", "1": "test_part1.py", "2": "test_part2.py", "all": "test_*.py"}[args.part]
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern=pattern, top_level_dir=str(root))
    print(f"Checking CANDIDATE: part {args.part}", flush=True)
    if args.part != "setup":
        print("The four starter TODOs intentionally fail until you implement them.", flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
