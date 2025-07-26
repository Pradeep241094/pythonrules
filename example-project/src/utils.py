#!/usr/bin/env python3
"""
Utility functions for the example project.
"""

import os
import json


def is_even(number):
    """Check if a number is even."""
    return number % 2 == 0


def is_odd(number):
    """Check if a number is odd."""
    return number % 2 != 0


def factorial(n):
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def save_to_file(data, filename):
    """Save data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def load_from_file(filename):
    """Load data from a JSON file."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")
    
    with open(filename, 'r') as f:
        return json.load(f)


def format_number(number, decimal_places=2):
    """Format a number to specified decimal places."""
    return round(number, decimal_places)