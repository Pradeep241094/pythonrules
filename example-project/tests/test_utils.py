#!/usr/bin/env python3
"""
Unit tests for the utils module.
"""

import unittest
import tempfile
import os
import sys

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import is_even, is_odd, factorial, save_to_file, load_from_file, format_number


class TestNumberUtils(unittest.TestCase):
    """Test cases for number utility functions."""
    
    def test_is_even_with_even_numbers(self):
        """Test is_even with even numbers."""
        self.assertTrue(is_even(2))
        self.assertTrue(is_even(4))
        self.assertTrue(is_even(0))
        self.assertTrue(is_even(-2))
    
    def test_is_even_with_odd_numbers(self):
        """Test is_even with odd numbers."""
        self.assertFalse(is_even(1))
        self.assertFalse(is_even(3))
        self.assertFalse(is_even(-1))
        self.assertFalse(is_even(-3))
    
    def test_is_odd_with_odd_numbers(self):
        """Test is_odd with odd numbers."""
        self.assertTrue(is_odd(1))
        self.assertTrue(is_odd(3))
        self.assertTrue(is_odd(-1))
        self.assertTrue(is_odd(-3))
    
    def test_is_odd_with_even_numbers(self):
        """Test is_odd with even numbers."""
        self.assertFalse(is_odd(2))
        self.assertFalse(is_odd(4))
        self.assertFalse(is_odd(0))
        self.assertFalse(is_odd(-2))
    
    def test_factorial_positive_numbers(self):
        """Test factorial with positive numbers."""
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(1), 1)
        self.assertEqual(factorial(2), 2)
        self.assertEqual(factorial(3), 6)
        self.assertEqual(factorial(4), 24)
        self.assertEqual(factorial(5), 120)
    
    def test_factorial_negative_number_raises_error(self):
        """Test that factorial with negative number raises error."""
        with self.assertRaises(ValueError) as context:
            factorial(-1)
        self.assertEqual(str(context.exception), "Factorial is not defined for negative numbers")
    
    def test_format_number_default_precision(self):
        """Test format_number with default precision."""
        result = format_number(3.14159)
        self.assertEqual(result, 3.14)
    
    def test_format_number_custom_precision(self):
        """Test format_number with custom precision."""
        result = format_number(3.14159, 3)
        self.assertEqual(result, 3.142)
    
    def test_format_number_zero_precision(self):
        """Test format_number with zero precision."""
        result = format_number(3.14159, 0)
        self.assertEqual(result, 3)


class TestFileUtils(unittest.TestCase):
    """Test cases for file utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test_data.json')
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.unlink(self.test_file)
        os.rmdir(self.temp_dir)
    
    def test_save_and_load_file(self):
        """Test saving and loading data to/from file."""
        test_data = {
            'name': 'Test User',
            'age': 30,
            'scores': [85, 92, 78]
        }
        
        # Save data
        save_to_file(test_data, self.test_file)
        self.assertTrue(os.path.exists(self.test_file))
        
        # Load data
        loaded_data = load_from_file(self.test_file)
        self.assertEqual(loaded_data, test_data)
    
    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises error."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        
        with self.assertRaises(FileNotFoundError) as context:
            load_from_file(nonexistent_file)
        self.assertIn('not found', str(context.exception))
    
    def test_save_empty_data(self):
        """Test saving empty data."""
        empty_data = {}
        save_to_file(empty_data, self.test_file)
        
        loaded_data = load_from_file(self.test_file)
        self.assertEqual(loaded_data, empty_data)
    
    def test_save_list_data(self):
        """Test saving list data."""
        list_data = [1, 2, 3, 'test', {'nested': 'value'}]
        save_to_file(list_data, self.test_file)
        
        loaded_data = load_from_file(self.test_file)
        self.assertEqual(loaded_data, list_data)


if __name__ == '__main__':
    unittest.main()