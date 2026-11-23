"""Provided test runner. Checks start and stop their own local HTTP service."""

import argparse
import unittest

import test_exercise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--part", choices=("setup", "1", "2", "all"), default="all")
    args = parser.parse_args()
    groups = {
        "setup": test_exercise.SetupTests,
        "1": test_exercise.Part1Tests,
        "2": test_exercise.Part2Tests,
    }
    selected = groups.values() if args.part == "all" else [groups[args.part]]
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(group)
                               for group in selected)
    print(f"Checking part {args.part}. The two TODOs initially fail implementation checks.", flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
