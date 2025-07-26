#!/usr/bin/env python3
"""
Unit tests for calculator functionality.
These are fast, isolated tests that test individual functions.
"""

import unittest


class Calculator:
    """Simple calculator class for demonstration."""
    
    @staticmethod
    def add(a, b):
        """Add two numbers."""
        return a + b
    
    @staticmethod
    def subtract(a, b):
        """Subtract two numbers."""
        return a - b
    
    @staticmethod
    def multiply(a, b):
        """Multiply two numbers."""
        return a * b
    
    @staticmethod
    def divide(a, b):
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


class TestCalculator(unittest.TestCase):
    """Unit tests for Calculator class."""
    
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
    
    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        result = self.calc.subtract(5, 3)
        self.assertEqual(result, 2)
    
    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        result = self.calc.multiply(3, 4)
        self.assertEqual(result, 12)
    
    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        result = self.calc.multiply(5, 0)
        self.assertEqual(result, 0)
    
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


class TestMathOperations(unittest.TestCase):
    """Additional unit tests for math operations."""
    
    def test_addition_commutative(self):
        """Test that addition is commutative."""
        calc = Calculator()
        self.assertEqual(calc.add(3, 5), calc.add(5, 3))
    
    def test_multiplication_commutative(self):
        """Test that multiplication is commutative."""
        calc = Calculator()
        self.assertEqual(calc.multiply(3, 5), calc.multiply(5, 3))
    
    def test_subtraction_not_commutative(self):
        """Test that subtraction is not commutative."""
        calc = Calculator()
        self.assertNotEqual(calc.subtract(5, 3), calc.subtract(3, 5))


if __name__ == '__main__':
    unittest.main()