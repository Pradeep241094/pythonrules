#!/usr/bin/env python3
"""
Sample test file for testing the test discovery functionality.
"""

import unittest


class TestSample(unittest.TestCase):
    """Sample test class."""
    
    def test_simple_pass(self):
        """A simple test that passes."""
        self.assertEqual(1 + 1, 2)
    
    def test_another_pass(self):
        """Another simple test that passes."""
        self.assertTrue(True)
    
    def test_string_operations(self):
        """Test string operations."""
        self.assertEqual("hello".upper(), "HELLO")

def test_standalone_function():
    assert 2 + 2 == 4


if __name__ == '__main__':
    unittest.main()