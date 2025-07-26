#!/usr/bin/env python3
"""
Test file with some failures for testing error handling.
"""

import unittest


class TestWithFailures(unittest.TestCase):
    """Test class with some failures."""
    
    def test_pass(self):
        """A test that passes."""
        self.assertEqual(1 + 1, 2)
    
    def test_fail(self):
        """A test that fails."""
        self.assertEqual(1 + 1, 3)  # This will fail
    
    def test_error(self):
        """A test that has an error."""
        raise ValueError("This is a test error")
    
    def test_another_pass(self):
        """Another test that passes."""
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()