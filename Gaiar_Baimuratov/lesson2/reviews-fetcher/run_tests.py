#!/usr/bin/env python3
"""
Run all tests for the reviews-fetcher project.
"""
import unittest
import sys
from pathlib import Path

# Add the project directory to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    # Find all tests
    test_loader = unittest.TestLoader()
    tests_dir = Path(__file__).parent / "tests"
    test_suite = test_loader.discover(str(tests_dir))

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Exit with non-zero code if tests failed
    sys.exit(not result.wasSuccessful())
