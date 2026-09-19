"""Smoke test for fast integration validation of runner CLI and simulation pipeline."""

import unittest
from runner import run_smoke_test


class TestSmoke(unittest.TestCase):
    """Integration smoke test."""

    def test_smoke_pipeline(self):
        # Must execute without throwing exceptions
        run_smoke_test(seed=777)


if __name__ == "__main__":
    unittest.main()
