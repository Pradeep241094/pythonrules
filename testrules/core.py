#!/usr/bin/env python3
"""
Core classes and functionality for the lightweight test runner.
"""

import time
import unittest
import traceback
from typing import Dict, List, Optional, Any


class TestMethod:
    """
    Represents a test method.
    """
    def __init__(self, name, module, class_name=None, file_path=None):
        self.name = name
        self.module = module
        self.class_name = class_name
        self.file_path = file_path
        self.full_name = f"{module}.{class_name}.{name}" if class_name else f"{module}.{name}"
    
    def __str__(self):
        return self.full_name
    
    def __repr__(self):
        return f"TestMethod(name='{self.name}', module='{self.module}', class_name='{self.class_name}')"


class MethodResult:
    """
    Represents the result of executing a test method.
    """
    def __init__(self, method, status, duration, error=None, traceback_str=None):
        self.method = method
        self.status = status  # "pass", "fail", or "error"
        self.duration = duration
        self.error = error
        self.traceback_str = traceback_str
    
    def __str__(self):
        return f"{self.method.full_name} ... {self.status.upper()}"
    
    def __repr__(self):
        return f"MethodResult(method={self.method.full_name}, status='{self.status}', duration={self.duration})"


class TestResult:
    """
    Container for test results.
    """
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.method_results = []
        self.duration = 0.0
        self.start_time = None
        self.end_time = None
    
    def add_result(self, method_result):
        """
        Add a method result to the test results.
        
        Args:
            method_result: MethodResult object to add
        """
        self.method_results.append(method_result)
        self.total += 1
        
        if method_result.status == "pass":
            self.passed += 1
        elif method_result.status == "fail":
            self.failed += 1
        elif method_result.status == "error":
            self.errors += 1
    
    def start_timing(self):
        """Start timing the test run."""
        self.start_time = time.time()
    
    def stop_timing(self):
        """Stop timing the test run and calculate duration."""
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
    
    def get_success_rate(self):
        """
        Calculate the success rate as a percentage.
        
        Returns:
            Success rate as a float (0.0 to 100.0)
        """
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100.0
    
    def get_failed_results(self):
        """
        Get all failed and error method results.
        
        Returns:
            List of MethodResult objects with status 'fail' or 'error'
        """
        return [result for result in self.method_results if result.status in ['fail', 'error']]
    
    def __str__(self):
        return f"TestResult(total={self.total}, passed={self.passed}, failed={self.failed}, errors={self.errors})"


class Config:
    """
    Configuration for the test runner.
    """
    def __init__(self, data=None):
        self.data = data or {}
        self.test_patterns = self.data.get("test_patterns", {
            "unit": ["test_*.py", "*_test.py"],
            "integration": ["integration_test_*.py", "*_integration_test.py"],
            "e2e": ["e2e_test_*.py", "*_e2e_test.py"],
            "regression": ["regression_test_*.py", "*_regression_test.py"]
        })
        self.test_groups = self.data.get("test_groups", {"all": []})
        self.coverage_enabled = self.data.get("coverage_enabled", True)
        self.html_coverage = self.data.get("html_coverage", True)
        self.html_coverage_dir = self.data.get("html_coverage_dir", "htmlcov")
        
        # Additional configuration options
        self.coverage_config = self.data.get("coverage_config", {})
        self.lint_config = self.data.get("lint_config", {})
        self.reporting = self.data.get("reporting", {})
        self.execution = self.data.get("execution", {})
        self.discovery = self.data.get("discovery", {})
    
    def get_test_types(self):
        """
        Get all available test types.
        
        Returns:
            List of test type names
        """
        return list(self.test_patterns.keys())
    
    def get_patterns_for_test_type(self, test_type):
        """
        Get file patterns for a specific test type.
        
        Args:
            test_type: The test type to get patterns for
            
        Returns:
            List of file patterns for the test type, or empty list if not found
        """
        return self.test_patterns.get(test_type, [])
    
    def has_test_type(self, test_type):
        """
        Check if a test type is configured.
        
        Args:
            test_type: The test type to check
            
        Returns:
            True if the test type is configured, False otherwise
        """
        return test_type in self.test_patterns
    
    def add_custom_test_type(self, test_type, patterns):
        """
        Add a custom test type with its patterns.
        
        Args:
            test_type: Name of the custom test type
            patterns: List of file patterns for the test type
        """
        self.test_patterns[test_type] = patterns
    
    def get_all_patterns(self):
        """
        Get all file patterns from all test types.
        
        Returns:
            List of all file patterns
        """
        all_patterns = []
        for patterns in self.test_patterns.values():
            all_patterns.extend(patterns)
        return list(set(all_patterns))  # Remove duplicates


class TestRunner:
    """
    Main test runner class that orchestrates test discovery and execution.
    """
    
    def __init__(self, config=None):
        """
        Initialize the test runner.
        
        Args:
            config: Config object, or None to use defaults
        """
        self.config = config or Config()
    
    def run_tests(self, test_type=None, modules=None, group=None, collect_coverage=None):
        """
        Run tests based on the specified criteria.
        
        Args:
            test_type: Type of tests to run (unit, integration, etc.)
            modules: List of specific modules to test
            group: Test group name to resolve from configuration
            collect_coverage: Whether to collect coverage (None = use config default)
            
        Returns:
            Tuple of (TestResult object, Coverage object or None)
        """
        from .discovery import discover_tests, discover_test_methods
        from .execution import run_tests as execute_tests
        
        # Use config default if not specified
        if collect_coverage is None:
            collect_coverage = self.config.coverage_enabled
        
        # Discover test files
        test_files = discover_tests(
            test_type=test_type,
            modules=modules, 
            group=group,
            config=self.config
        )
        
        if not test_files:
            print("❌ No test files found!")
            return TestResult(), None
        
        # Discover test methods
        test_methods_by_module = discover_test_methods(test_files)
        
        total_methods = sum(len(methods) for methods in test_methods_by_module.values())
        if total_methods == 0:
            print("❌ No test methods found!")
            return TestResult(), None
        
        # Execute tests
        return execute_tests(test_methods_by_module, collect_coverage, self.config)