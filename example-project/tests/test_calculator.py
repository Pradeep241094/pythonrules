#!/usr/bin/env python3
"""
Unit tests for the calculator module.
"""

import unittest
import sys
import os

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculator import Calculator, quick_add, quick_multiply


class TestCalculator(unittest.TestCase):
    """Test cases for the Calculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calc = Calculator()
    
    def test_add_positive_numbers(self):
        """Test adding positive numbers."""
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
    
    def test_add_negative_numbers(self):
        """Test adding negative numbers."""
        result = self.calc.add(-2, -3)
        self.assertEqual(result, -5)
    
    def test_add_mixed_numbers(self):
        """Test adding positive and negative numbers."""
        result = self.calc.add(5, -3)
        self.assertEqual(result, 2)
    
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        result = self.calc.subtract(5, 3)
        self.assertEqual(result, 2)
    
    def test_subtract_negative_numbers(self):
        """Test subtracting negative numbers."""
        result = self.calc.subtract(-5, -3)
        self.assertEqual(result, -2)
    
    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        result = self.calc.multiply(3, 4)
        self.assertEqual(result, 12)
    
    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        result = self.calc.multiply(5, 0)
        self.assertEqual(result, 0)
    
    def test_multiply_negative_numbers(self):
        """Test multiplying negative numbers."""
        result = self.calc.multiply(-3, -4)
        self.assertEqual(result, 12)
    
    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        result = self.calc.divide(10, 2)
        self.assertEqual(result, 5.0)
    
    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises an error."""
        with self.assertRaises(ValueError) as context:
            self.calc.divide(10, 0)
        self.assertEqual(str(context.exception), "Cannot divide by zero")
    
    def test_divide_negative_numbers(self):
        """Test dividing negative numbers."""
        result = self.calc.divide(-10, -2)
        self.assertEqual(result, 5.0)
    
    def test_history_tracking(self):
        """Test that operations are tracked in history."""
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        self.calc.multiply(2, 4)
        
        history = self.calc.get_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0], "1 + 2 = 3")
        self.assertEqual(history[1], "5 - 3 = 2")
        self.assertEqual(history[2], "2 * 4 = 8")
    
    def test_clear_history(self):
        """Test clearing calculation history."""
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        self.assertEqual(len(self.calc.get_history()), 2)
        
        self.calc.clear_history()
        self.assertEqual(len(self.calc.get_history()), 0)


class TestQuickFunctions(unittest.TestCase):
    """Test cases for quick calculation functions."""
    
    def test_quick_add(self):
        """Test quick add function."""
        result = quick_add(3, 7)
        self.assertEqual(result, 10)
    
    def test_quick_add_negative(self):
        """Test quick add with negative numbers."""
        result = quick_add(-3, 7)
        self.assertEqual(result, 4)
    
    def test_quick_multiply(self):
        """Test quick multiply function."""
        result = quick_multiply(3, 7)
        self.assertEqual(result, 21)
    
    def test_quick_multiply_zero(self):
        """Test quick multiply with zero."""
        result = quick_multiply(5, 0)
        self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()