#!/usr/bin/env python3
"""A clean test file with no style violations."""

import unittest


class TestClean(unittest.TestCase):
    """Test class with clean code."""

    def test_simple(self):
        """Test a simple assertion."""
        self.assertEqual(1 + 1, 2)

    def test_another(self):
        """Test another simple assertion."""
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
