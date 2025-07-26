#!/usr/bin/env python3
"""
Test file to demonstrate timing functionality.
"""

import unittest
import time


class TestTimingDemo(unittest.TestCase):
    """Test class to demonstrate timing."""
    
    def test_fast(self):
        """A fast test."""
        self.assertEqual(1 + 1, 2)
    
    def test_medium(self):
        """A medium speed test."""
        time.sleep(0.01)  # 10ms
        self.assertTrue(True)
    
    def test_slow(self):
        """A slow test."""
        time.sleep(0.05)  # 50ms
        self.assertEqual("hello".upper(), "HELLO")
    
    def test_very_slow(self):
        """A very slow test."""
        time.sleep(0.1)  # 100ms
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()