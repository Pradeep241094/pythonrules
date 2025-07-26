#!/usr/bin/env python3
"""
Lightweight Test Runner

A simple, efficient Python testing framework that provides test discovery at the method level,
code coverage reporting, and basic linting capabilities.
"""

__version__ = "1.0.0"
__author__ = "Test Runner Team"
__email__ = "team@example.com"
__description__ = "A lightweight Python test runner with method-level discovery and coverage reporting"

# Import main classes for easy access
from .core import (
    TestMethod,
    MethodResult, 
    TestResult,
    Config,
    TestRunner
)

# Import utility functions
from .discovery import (
    discover_tests,
    discover_test_methods,
    get_test_files_by_type
)

# Import CLI for programmatic access
from .cli import main as run_cli

__all__ = [
    'TestMethod',
    'MethodResult', 
    'TestResult',
    'Config',
    'TestRunner',
    'discover_tests',
    'discover_test_methods',
    'get_test_files_by_type',
    'run_cli',
    '__version__'
]