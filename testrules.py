#!/usr/bin/env python3
"""
Lightweight Test Runner

A simple, efficient Python testing framework that provides test discovery at the method level,
code coverage reporting, and basic linting capabilities.

Usage:
    python testrules.py [group|test_module1 test_module2 ...|lint|check|unit|integration|e2e|regression]

Examples:
    python testrules.py                    # Run all tests
    python testrules.py unit              # Run unit tests only
    python testrules.py integration       # Run integration tests only
    python testrules.py e2e               # Run end-to-end tests only
    python testrules.py regression        # Run regression tests only
    python testrules.py lint              # Run linting only
    python testrules.py check             # Run both linting and all tests
    python testrules.py core              # Run tests in 'core' group (if defined in config)
    python testrules.py test_module1 test_module2  # Run specific test modules
"""

import sys
import os
import json
import time
import unittest
import importlib
import importlib.util
import glob
from typing import Dict, List, Optional, Any, Tuple
import traceback

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    print("Warning: coverage package not available. Install with: pip install coverage")

try:
    import flake8.api.legacy as flake8
    FLAKE8_AVAILABLE = True
except ImportError:
    FLAKE8_AVAILABLE = False
    print("Warning: flake8 package not available. Install with: pip install flake8")


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


def get_test_files_by_type(test_type, config, search_path="."):
    """
    Get test files for a specific test type based on configured patterns.
    
    Args:
        test_type: The test type to get files for
        config: Config object containing test patterns
        search_path: Directory to search in (default: current directory)
        
    Returns:
        List of test file paths matching the test type patterns
    """
    if not config.has_test_type(test_type):
        print(f"⚠️ Unknown test type: {test_type}")
        return []
    
    patterns = config.get_patterns_for_test_type(test_type)
    test_files = []
    
    for pattern in patterns:
        # Search recursively for files matching the pattern
        search_pattern = os.path.join(search_path, "**", pattern)
        matching_files = glob.glob(search_pattern, recursive=True)
        test_files.extend(matching_files)
    
    # Remove duplicates and sort
    test_files = sorted(list(set(test_files)))
    
    return test_files


def get_all_test_files(config, search_path="."):
    """
    Get all test files based on all configured patterns.
    
    Args:
        config: Config object containing test patterns
        search_path: Directory to search in (default: current directory)
        
    Returns:
        Dictionary mapping test types to their test files
    """
    all_test_files = {}
    
    for test_type in config.get_test_types():
        test_files = get_test_files_by_type(test_type, config, search_path)
        if test_files:
            all_test_files[test_type] = test_files
    
    return all_test_files


def discover_files_by_modules(module_names, search_path="."):
    """
    Discover test files by explicit module names.
    
    Args:
        module_names: List of module names to discover
        search_path: Directory to search in (default: current directory)
        
    Returns:
        List of test file paths for the specified modules
    """
    test_files = []
    
    for module_name in module_names:
        # Try different possible file paths for the module
        possible_paths = [
            f"{module_name}.py",
            os.path.join(search_path, f"{module_name}.py"),
            os.path.join(search_path, "**", f"{module_name}.py"),
        ]
        
        found = False
        for path in possible_paths:
            if "**" in path:
                # Use glob for recursive search
                matching_files = glob.glob(path, recursive=True)
                if matching_files:
                    test_files.extend(matching_files)
                    found = True
                    break
            else:
                # Direct file check
                if os.path.exists(path):
                    test_files.append(path)
                    found = True
                    break
        
        if not found:
            print(f"⚠️ Module file not found: {module_name}")
    
    # Remove duplicates and sort
    return sorted(list(set(test_files)))


def resolve_test_group(group_name, config):
    """
    Resolve a test group to get the list of modules in that group.
    
    Args:
        group_name: Name of the test group
        config: Config object containing test groups
        
    Returns:
        List of module names in the group, or empty list if group not found
    """
    if group_name not in config.test_groups:
        print(f"⚠️ Test group '{group_name}' not found in configuration")
        return []
    
    modules = config.test_groups[group_name]
    print(f"📋 Test group '{group_name}' contains {len(modules)} modules: {modules}")
    return modules


def discover_tests(test_type=None, modules=None, group=None, config=None, search_path="."):
    """
    Discover test files and methods based on various criteria.
    
    Args:
        test_type: Type of tests to discover (unit, integration, e2e, regression)
        modules: List of specific modules to test
        group: Test group name to resolve from configuration
        config: Configuration object
        search_path: Directory to search in (default: current directory)
        
    Returns:
        List of test file paths
    """
    if config is None:
        config = Config()
    
    test_files = []
    
    # Priority order: explicit modules > test group > test type > all tests
    if modules:
        print(f"🎯 Discovering tests for explicit modules: {modules}")
        test_files = discover_files_by_modules(modules, search_path)
    elif group:
        print(f"📋 Discovering tests for group: {group}")
        group_modules = resolve_test_group(group, config)
        if group_modules:
            test_files = discover_files_by_modules(group_modules, search_path)
        else:
            print(f"⚠️ No modules found in group '{group}' or group doesn't exist")
    elif test_type:
        print(f"🔍 Discovering tests for type: {test_type}")
        test_files = get_test_files_by_type(test_type, config, search_path)
    else:
        print("🔍 Discovering all test files")
        all_test_files = get_all_test_files(config, search_path)
        for files in all_test_files.values():
            test_files.extend(files)
        # Remove duplicates
        test_files = sorted(list(set(test_files)))
    
    print(f"📁 Found {len(test_files)} test files")
    return test_files


def safe_import_module(module_name, file_path=None):
    """
    Safely import a module with comprehensive error handling.
    
    Args:
        module_name: Name of the module to import
        file_path: Optional file path of the module for dynamic loading
        
    Returns:
        Tuple of (module, success_flag, error_message)
    """
    try:
        if file_path and os.path.exists(file_path):
            # Dynamic module loading from file path
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                
                # Add the module's directory to sys.path temporarily
                module_dir = os.path.dirname(os.path.abspath(file_path))
                if module_dir not in sys.path:
                    sys.path.insert(0, module_dir)
                    path_added = True
                else:
                    path_added = False
                
                try:
                    spec.loader.exec_module(module)
                    return module, True, None
                finally:
                    # Remove the added path
                    if path_added:
                        sys.path.remove(module_dir)
            else:
                return None, False, f"Could not create module spec for {module_name} at {file_path}"
        else:
            # Standard module import
            module = importlib.import_module(module_name)
            return module, True, None
            
    except ImportError as e:
        return None, False, f"ImportError: {e}"
    except SyntaxError as e:
        return None, False, f"SyntaxError in {module_name}: {e}"
    except Exception as e:
        return None, False, f"Unexpected error importing {module_name}: {e}"


def inspect_module_for_tests(module_name, file_path=None):
    """
    Inspect a module to find test methods using reflection with safe importing.
    
    Args:
        module_name: Name of the module to inspect
        file_path: Optional file path of the module
        
    Returns:
        List of TestMethod objects found in the module
    """
    test_methods = []
    
    # Safely import the module
    module, success, error_msg = safe_import_module(module_name, file_path)
    
    if not success:
        print(f"⚠️ Failed to import module {module_name}: {error_msg}")
        return test_methods
    
    try:
        # Find all classes in the module
        for attr_name in dir(module):
            try:
                attr = getattr(module, attr_name)
                
                # Check if it's a class and inherits from unittest.TestCase
                if (isinstance(attr, type) and 
                    issubclass(attr, unittest.TestCase) and 
                    attr != unittest.TestCase):
                    
                    class_name = attr_name
                    
                    # Find all test methods in the class
                    for method_name in dir(attr):
                        if method_name.startswith('test'):
                            try:
                                method_obj = getattr(attr, method_name)
                                if callable(method_obj):
                                    test_method = TestMethod(
                                        name=method_name,
                                        module=module_name,
                                        class_name=class_name,
                                        file_path=file_path
                                    )
                                    test_methods.append(test_method)
                            except Exception as e:
                                print(f"⚠️ Error accessing method {method_name} in {class_name}: {e}")
                                continue
                                
            except Exception as e:
                print(f"⚠️ Error accessing attribute {attr_name} in module {module_name}: {e}")
                continue
        
        # Also check for standalone test functions (not in classes)
        for attr_name in dir(module):
            if attr_name.startswith('test'):
                try:
                    attr = getattr(module, attr_name)
                    # Make sure it's a function and not a class
                    if callable(attr) and not isinstance(attr, type):
                        test_method = TestMethod(
                            name=attr_name,
                            module=module_name,
                            class_name=None,
                            file_path=file_path
                        )
                        test_methods.append(test_method)
                except Exception as e:
                    print(f"⚠️ Error accessing function {attr_name} in module {module_name}: {e}")
                    continue
    
    except Exception as e:
        print(f"⚠️ Error inspecting module {module_name}: {e}")
    
    return test_methods


def discover_test_methods(test_files):
    """
    Discover test methods from a list of test files with graceful error handling.
    
    Args:
        test_files: List of test file paths
        
    Returns:
        Dictionary mapping module names to lists of TestMethod objects
    """
    test_methods_by_module = {}
    failed_modules = []
    
    for file_path in test_files:
        # Convert file path to module name
        # Normalize the path and remove leading ./
        normalized_path = os.path.normpath(file_path)
        if normalized_path.startswith('./'):
            normalized_path = normalized_path[2:]
        
        # Convert to module name
        module_name = normalized_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        
        # Remove leading dots
        while module_name.startswith('.'):
            module_name = module_name[1:]
        
        print(f"🔍 Inspecting module: {module_name} ({file_path})")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            failed_modules.append(module_name)
            continue
        
        # Inspect the module for test methods
        test_methods = inspect_module_for_tests(module_name, file_path)
        
        if test_methods:
            test_methods_by_module[module_name] = test_methods
            print(f"   ✅ Found {len(test_methods)} test methods:")
            for method in test_methods:
                print(f"     - {method.full_name}")
        else:
            print(f"   ℹ️ No test methods found in {module_name}")
    
    # Report summary
    total_modules = len(test_files)
    successful_modules = len(test_methods_by_module)
    failed_count = len(failed_modules)
    
    print(f"\n📊 Module Discovery Summary:")
    print(f"   Total modules processed: {total_modules}")
    print(f"   Successfully imported: {successful_modules}")
    print(f"   Failed to import: {failed_count}")
    
    if failed_modules:
        print(f"   Failed modules: {failed_modules}")
    
    return test_methods_by_module


def run_single_test_method(test_method):
    """
    Run a single test method and collect its result.
    
    Args:
        test_method: TestMethod object to run
        
    Returns:
        MethodResult object containing the test result
    """
    start_time = time.time()
    
    try:
        # Import the module containing the test
        module, success, error_msg = safe_import_module(test_method.module, test_method.file_path)
        
        if not success:
            duration = time.time() - start_time
            return MethodResult(
                method=test_method,
                status="error",
                duration=duration,
                error=f"Failed to import module: {error_msg}",
                traceback_str=None
            )
        
        # Get the test class and method
        if test_method.class_name:
            # Test method is in a class
            test_class = getattr(module, test_method.class_name)
            
            # Create a test suite with just this method
            suite = unittest.TestSuite()
            test_instance = test_class(test_method.name)
            suite.addTest(test_instance)
        else:
            # Standalone test function - create a wrapper
            test_func = getattr(module, test_method.name)
            
            # Create a test case wrapper for the function
            class FunctionTestCase(unittest.TestCase):
                def runTest(self):
                    test_func()
            
            suite = unittest.TestSuite()
            suite.addTest(FunctionTestCase())
        
        # Run the test with a custom result collector
        result = unittest.TestResult()
        suite.run(result)
        
        duration = time.time() - start_time
        
        # Determine the status and extract error information
        if result.wasSuccessful():
            return MethodResult(
                method=test_method,
                status="pass",
                duration=duration,
                error=None,
                traceback_str=None
            )
        elif result.failures:
            # Test failed (assertion error)
            failure = result.failures[0]  # Get first failure
            error_msg = str(failure[1])
            traceback_str = failure[1]
            
            return MethodResult(
                method=test_method,
                status="fail",
                duration=duration,
                error=error_msg,
                traceback_str=traceback_str
            )
        elif result.errors:
            # Test had an error (exception)
            error = result.errors[0]  # Get first error
            error_msg = str(error[1])
            traceback_str = error[1]
            
            return MethodResult(
                method=test_method,
                status="error",
                duration=duration,
                error=error_msg,
                traceback_str=traceback_str
            )
        else:
            # Shouldn't happen, but handle gracefully
            return MethodResult(
                method=test_method,
                status="error",
                duration=duration,
                error="Unknown test result state",
                traceback_str=None
            )
            
    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        
        return MethodResult(
            method=test_method,
            status="error",
            duration=duration,
            error=error_msg,
            traceback_str=traceback_str
        )


def start_coverage_collection(config):
    """
    Initialize and start coverage collection with proper configuration.
    
    Args:
        config: Config object containing coverage settings
        
    Returns:
        Coverage object if successful, None otherwise
    """
    if not COVERAGE_AVAILABLE:
        print("⚠️ Coverage package not available. Install with: pip install coverage")
        return None
    
    try:
        # Initialize coverage with configuration
        cov = coverage.Coverage(
            branch=True,  # Enable branch coverage
            source=['.'],  # Cover current directory
            omit=[
                '*/tests/*',  # Exclude test files from coverage
                '*/test_*',   # Exclude test files
                '*_test.py',  # Exclude test files
                'setup.py',   # Exclude setup files
                '*/venv/*',   # Exclude virtual environment
                '*/env/*',    # Exclude virtual environment
                '*/.venv/*',  # Exclude virtual environment
            ]
        )
        
        # Start coverage collection
        cov.start()
        print("📊 Coverage collection started with branch coverage enabled")
        return cov
        
    except Exception as e:
        print(f"⚠️ Failed to initialize coverage collection: {e}")
        return None


def stop_coverage_collection(cov):
    """
    Stop coverage collection and save data.
    
    Args:
        cov: Coverage object to stop
        
    Returns:
        True if successful, False otherwise
    """
    if not cov:
        return False
    
    try:
        cov.stop()
        cov.save()
        print("📊 Coverage collection completed and data saved")
        return True
        
    except Exception as e:
        print(f"⚠️ Error stopping coverage collection: {e}")
        return False


def generate_coverage_report(cov):
    """
    Generate console coverage report with line and branch coverage.
    
    Args:
        cov: Coverage object containing coverage data
        
    Returns:
        Dictionary containing coverage summary data
    """
    if not cov:
        print("⚠️ No coverage data available")
        return None
    
    try:
        # Get coverage data
        coverage_data = cov.get_data()
        
        if not coverage_data.measured_files():
            print("⚠️ No files were measured for coverage")
            return None
        
        # Generate coverage report
        print("\n📊 COVERAGE REPORT")
        print("=" * 60)
        
        # Print header
        print(f"{'Name':<30} {'Stmts':<8} {'Miss':<8} {'Branch':<8} {'BrPart':<8} {'Cover':<8}")
        print("-" * 60)
        
        total_statements = 0
        total_missing = 0
        total_branches = 0
        total_partial_branches = 0
        
        # Get coverage analysis for each file
        for filename in sorted(coverage_data.measured_files()):
            try:
                # Get analysis for this file - analysis2 returns a tuple
                analysis_result = cov.analysis2(filename)
                
                # analysis2 returns (filename, statements, excluded, missing, missing_formatted)
                if len(analysis_result) >= 4:
                    _, statements_list, _, missing_list = analysis_result[:4]
                    statements = len(statements_list)
                    missing = len(missing_list)
                else:
                    # Fallback to basic analysis
                    statements = 0
                    missing = 0
                    missing_list = []
                
                # Get branch coverage if available
                try:
                    branch_stats = cov.branch_stats().get(filename, (0, 0, 0))
                    branches = branch_stats[0] if len(branch_stats) > 0 else 0
                    partial_branches = branch_stats[1] if len(branch_stats) > 1 else 0
                except:
                    branches = 0
                    partial_branches = 0
                
                # Calculate coverage percentage
                if statements > 0:
                    coverage_percent = ((statements - missing) / statements) * 100
                else:
                    coverage_percent = 100.0
                
                # Accumulate totals
                total_statements += statements
                total_missing += missing
                total_branches += branches
                total_partial_branches += partial_branches
                
                # Format filename for display
                display_name = filename
                if len(display_name) > 28:
                    display_name = "..." + display_name[-25:]
                
                # Print file coverage
                print(f"{display_name:<30} {statements:<8} {missing:<8} {branches:<8} {partial_branches:<8} {coverage_percent:>6.1f}%")
                
                # Show missing lines if there are any
                if missing > 0 and len(missing_list) <= 10:  # Only show if not too many
                    missing_lines = sorted(missing_list)
                    missing_ranges = []
                    
                    if missing_lines:
                        # Group consecutive lines into ranges
                        start = missing_lines[0]
                        end = start
                        
                        for line in missing_lines[1:]:
                            if line == end + 1:
                                end = line
                            else:
                                if start == end:
                                    missing_ranges.append(str(start))
                                else:
                                    missing_ranges.append(f"{start}-{end}")
                                start = end = line
                        
                        # Add the last range
                        if start == end:
                            missing_ranges.append(str(start))
                        else:
                            missing_ranges.append(f"{start}-{end}")
                        
                        print(f"{'':<30} Missing: {', '.join(missing_ranges)}")
                
            except Exception as e:
                print(f"⚠️ Error analyzing coverage for {filename}: {e}")
                continue
        
        # Print totals
        print("-" * 60)
        
        # Calculate total coverage
        if total_statements > 0:
            total_coverage = ((total_statements - total_missing) / total_statements) * 100
        else:
            total_coverage = 100.0
        
        print(f"{'TOTAL':<30} {total_statements:<8} {total_missing:<8} {total_branches:<8} {total_partial_branches:<8} {total_coverage:>6.1f}%")
        
        # Coverage summary
        print(f"\n📈 COVERAGE SUMMARY:")
        print(f"   Lines covered: {total_statements - total_missing}/{total_statements} ({total_coverage:.1f}%)")
        if total_branches > 0:
            branch_coverage = ((total_branches - total_partial_branches) / total_branches) * 100 if total_branches > 0 else 100.0
            print(f"   Branches covered: {total_branches - total_partial_branches}/{total_branches} ({branch_coverage:.1f}%)")
        
        # Return summary data
        return {
            'total_statements': total_statements,
            'total_missing': total_missing,
            'total_branches': total_branches,
            'total_partial_branches': total_partial_branches,
            'line_coverage': total_coverage,
            'branch_coverage': ((total_branches - total_partial_branches) / total_branches) * 100 if total_branches > 0 else 100.0
        }
        
    except Exception as e:
        print(f"⚠️ Error generating coverage report: {e}")
        return None


def generate_html_coverage_report(cov, config):
    """
    Generate HTML coverage report using coverage package.
    
    Args:
        cov: Coverage object containing coverage data
        config: Config object containing HTML coverage settings
        
    Returns:
        True if successful, False otherwise
    """
    if not cov:
        print("⚠️ No coverage data available for HTML report")
        return False
    
    if not config.html_coverage:
        print("ℹ️ HTML coverage report generation is disabled in configuration")
        return False
    
    try:
        # Ensure the HTML coverage directory exists
        html_dir = config.html_coverage_dir
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
            print(f"📁 Created HTML coverage directory: {html_dir}")
        
        # Generate HTML report
        print(f"📄 Generating HTML coverage report...")
        cov.html_report(directory=html_dir)
        
        # Get the path to the main HTML file
        index_path = os.path.join(html_dir, 'index.html')
        
        if os.path.exists(index_path):
            # Convert to absolute path for better display
            abs_index_path = os.path.abspath(index_path)
            print(f"📁 HTML coverage report saved to: {abs_index_path}")
            print(f"🌐 Open in browser: file://{abs_index_path}")
            return True
        else:
            print(f"⚠️ HTML report was generated but index.html not found at expected location")
            return False
        
    except Exception as e:
        print(f"⚠️ Error generating HTML coverage report: {e}")
        return False


def run_tests(test_methods_by_module, collect_coverage=True, config=None):
    """
    Run tests and collect results.
    
    Args:
        test_methods_by_module: Dictionary mapping module names to lists of TestMethod objects
        collect_coverage: Whether to collect coverage information
        config: Config object containing coverage settings
        
    Returns:
        Tuple of (TestResult object, Coverage object or None)
    """
    print("🧪 Starting test execution...")
    
    # Initialize test results
    test_result = TestResult()
    test_result.start_timing()
    
    # Initialize coverage if requested
    cov = None
    if collect_coverage:
        if config is None:
            config = Config()
        cov = start_coverage_collection(config)
    
    # Count total test methods
    total_methods = sum(len(methods) for methods in test_methods_by_module.values())
    print(f"🎯 Running {total_methods} test methods across {len(test_methods_by_module)} modules")
    
    current_method = 0
    
    # Run tests for each module
    for module_name, test_methods in test_methods_by_module.items():
        print(f"\n📦 Running tests in module: {module_name}")
        
        for test_method in test_methods:
            current_method += 1
            print(f"  [{current_method}/{total_methods}] {test_method.full_name} ... ", end="", flush=True)
            
            # Run the test method
            method_result = run_single_test_method(test_method)
            
            # Add result to test results
            test_result.add_result(method_result)
            
            # Print result with timing
            if method_result.status == "pass":
                print(f"✅ PASS ({method_result.duration:.3f}s)")
            elif method_result.status == "fail":
                print(f"❌ FAIL ({method_result.duration:.3f}s)")
            elif method_result.status == "error":
                print(f"💥 ERROR ({method_result.duration:.3f}s)")
    
    # Stop timing
    test_result.stop_timing()
    
    # Stop coverage collection if it was started
    stop_coverage_collection(cov)
    
    print(f"\n⏱️ Test execution completed in {test_result.duration:.2f} seconds")
    
    return test_result, cov


def run_lint(search_path=".", specific_files=None):
    """
    Run PEP8 style checks using flake8.
    
    Args:
        search_path: Directory to search for Python files (default: current directory)
        specific_files: List of specific files to check (optional)
        
    Returns:
        Number of style violations found
    """
    if not FLAKE8_AVAILABLE:
        print("⚠️ flake8 package not available. Install with: pip install flake8")
        return -1
    
    try:
        print("🔍 Running code style checks with flake8...")
        
        # Initialize flake8 style guide
        style_guide = flake8.get_style_guide()
        
        # Determine which files to check
        if specific_files:
            python_files = [f for f in specific_files if f.endswith('.py') and os.path.exists(f)]
        else:
            # Find all Python files to check
            python_files = []
            for root, dirs, files in os.walk(search_path):
                # Skip common directories that shouldn't be linted
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'htmlcov', '.coverage', 'venv', 'env', '.venv', '.env']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        python_files.append(file_path)
        
        if not python_files:
            print("⚠️ No Python files found to lint")
            return 0
        
        print(f"📁 Found {len(python_files)} Python files to check")
        
        # Run flake8 checks
        report = style_guide.check_files(python_files)
        
        # Get the number of violations from the report statistics
        error_stats = report.get_statistics('E')
        warning_stats = report.get_statistics('W')
        flake_stats = report.get_statistics('F')
        
        # Count total violations
        violation_count = len(error_stats) + len(warning_stats) + len(flake_stats)
        
        return violation_count
        
    except Exception as e:
        print(f"⚠️ Error running flake8 checks: {e}")
        return -1


def report_lint_results(violation_count):
    """
    Display lint results with appropriate formatting.
    
    Args:
        violation_count: Number of style violations found (-1 if error occurred)
    """
    print("\n" + "=" * 60)
    print("🔍 LINT RESULTS")
    print("=" * 60)
    
    if violation_count == -1:
        print("❌ Linting failed due to an error")
        print("📋 Please check the error message above for details")
    elif violation_count == 0:
        print("✅ No style violations found! Code follows PEP8 standards.")
        print("🎉 Your code is clean and well-formatted!")
    else:
        print(f"⚠️ Found {violation_count} style violation{'s' if violation_count != 1 else ''}")
        print("📋 Check the output above for details on violations")
        print("💡 Run a code formatter like 'black' or 'autopep8' to fix many issues automatically")


def load_config(config_file="testrules.json"):
    """
    Load configuration from a JSON file if present, else use defaults.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Config object containing configuration settings
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                data = json.load(f)
            print(f"📄 Loaded configuration from {config_file}")
            return Config(data)
        else:
            print(f"📄 No configuration file found at {config_file}, using defaults")
            return Config()
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing configuration file {config_file}: {e}")
        print("📄 Using default configuration")
        return Config()
    except Exception as e:
        print(f"⚠️ Error loading configuration file {config_file}: {e}")
        print("📄 Using default configuration")
        return Config()


def report_test_summary(test_results):
    """
    Display test summary reporting with total tests, passed, failed counts,
    success rate percentage, and execution time information.
    
    Args:
        test_results: TestResult object containing test results
        
    Requirements: 2.1, 2.2, 2.3, 2.5
    """
    print("\n" + "=" * 60)
    print("🧪 TEST SUMMARY")
    print("=" * 60)
    
    # Display total tests, passed, and failed counts (Requirements 2.1, 2.2)
    print(f"✅ Passed:        {test_results.passed}")
    print(f"❌ Failed:        {test_results.failed}")
    print(f"💥 Errors:        {test_results.errors}")
    print(f"📊 Total:         {test_results.total}")
    
    # Calculate and show success rate as percentage (Requirement 2.3)
    success_rate = test_results.get_success_rate()
    print(f"📈 Success Rate:  {success_rate:.2f}%")
    
    # Show execution time information (Requirement 2.5)
    print(f"⏱️  Execution Time: {test_results.duration:.2f} seconds")
    
    # Visual indicator based on results
    if test_results.failed == 0 and test_results.errors == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {test_results.failed + test_results.errors} test(s) failed or had errors")


def report_detailed_test_results(test_results):
    """
    Show individual test method results with full qualified names,
    display error details and tracebacks for failed tests,
    and format output with emoji and clear visual separation.
    
    Args:
        test_results: TestResult object containing test results
        
    Requirements: 2.4
    """
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 60)
    
    # Show individual test method results with full qualified names
    for result in test_results.method_results:
        status_emoji = "✅" if result.status == "pass" else ("❌" if result.status == "fail" else "💥")
        status_text = result.status.upper()
        
        print(f"{status_emoji} {result.method.full_name} ... {status_text} ({result.duration:.3f}s)")
    
    # Display error details and tracebacks for failed tests
    failed_results = test_results.get_failed_results()
    if failed_results:
        print("\n" + "=" * 60)
        print("❌ FAILURE DETAILS")
        print("=" * 60)
        
        for i, result in enumerate(failed_results, 1):
            print(f"\n{i}. {result.method.full_name}")
            print("-" * 60)
            
            if result.status == "fail":
                print("FAILURE:")
            elif result.status == "error":
                print("ERROR:")
            
            # Display error details with proper formatting
            if result.error:
                print(result.error)
            
            # Display traceback if available
            if result.traceback_str:
                print("\nTraceback:")
                print(result.traceback_str)
            
            if i < len(failed_results):
                print("\n" + "-" * 60)


def show_help():
    """
    Display help information for the test runner.
    """
    help_text = """
🚀 Lightweight Test Runner

USAGE:
    python testrules.py [COMMAND|MODULE...]

COMMANDS:
    (no args)           Run all tests
    unit               Run unit tests only
    integration        Run integration tests only  
    e2e                Run end-to-end tests only
    regression         Run regression tests only
    lint               Run code style checks only
    check              Run both linting and all tests
    help, --help, -h   Show this help message

TEST GROUPS:
    You can run predefined test groups from your configuration file:
    python testrules.py [GROUP_NAME]

MODULES:
    Run specific test modules:
    python testrules.py module1 module2 ...

EXAMPLES:
    python testrules.py                    # Run all tests
    python testrules.py unit              # Run unit tests only
    python testrules.py integration       # Run integration tests only
    python testrules.py e2e               # Run end-to-end tests only
    python testrules.py regression        # Run regression tests only
    python testrules.py lint              # Run linting only
    python testrules.py check             # Run both linting and all tests
    python testrules.py core              # Run tests in 'core' group (if defined in config)
    python testrules.py test_module1 test_module2  # Run specific test modules

CONFIGURATION:
    Configuration is loaded from testrules.json if present.
    See documentation for configuration options.
    """
    print(help_text)


def parse_arguments(args, config):
    """
    Parse command-line arguments and determine what action to take.
    
    Args:
        args: List of command-line arguments
        config: Config object containing test types and groups
        
    Returns:
        Dictionary containing parsed arguments with keys:
        - action: 'help', 'lint', 'check', 'test'
        - test_type: Test type name or None
        - modules: List of module names or None
        - group: Test group name or None
        - command_description: Human-readable description of the command
    """
    if not args:
        return {
            'action': 'test',
            'test_type': None,
            'modules': None,
            'group': None,
            'command_description': 'all tests'
        }
    
    # Handle help commands
    if len(args) == 1 and args[0] in ['help', '--help', '-h']:
        return {
            'action': 'help',
            'test_type': None,
            'modules': None,
            'group': None,
            'command_description': 'help'
        }
    
    # Handle single argument commands
    if len(args) == 1:
        command = args[0]
        
        # Special commands
        if command == "lint":
            return {
                'action': 'lint',
                'test_type': None,
                'modules': None,
                'group': None,
                'command_description': 'linting only'
            }
        elif command == "check":
            return {
                'action': 'check',
                'test_type': None,
                'modules': None,
                'group': None,
                'command_description': 'comprehensive check (linting + all tests)'
            }
        # Test type commands
        elif command in config.get_test_types():
            return {
                'action': 'test',
                'test_type': command,
                'modules': None,
                'group': None,
                'command_description': f'{command} tests'
            }
        # Test group commands
        elif command in config.test_groups:
            return {
                'action': 'test',
                'test_type': None,
                'modules': None,
                'group': command,
                'command_description': f'test group "{command}"'
            }
        # Single module
        else:
            return {
                'action': 'test',
                'test_type': None,
                'modules': [command],
                'group': None,
                'command_description': f'module "{command}"'
            }
    
    # Multiple arguments - treat as modules
    return {
        'action': 'test',
        'test_type': None,
        'modules': args,
        'group': None,
        'command_description': f'modules: {", ".join(args)}'
    }


def main():
    """
    Main entry point for the test runner.
    
    Usage:
        python testrules.py [group|test_module1 test_module2 ...|lint|check|unit|integration|e2e|regression]
    """
    print("🚀 Lightweight Test Runner")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    
    # Parse command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    parsed_args = parse_arguments(args, config)
    
    # Handle help command
    if parsed_args['action'] == 'help':
        show_help()
        return 0
    
    # Handle lint command
    if parsed_args['action'] == 'lint':
        print("🔍 Running code style checks...")
        violation_count = run_lint()
        report_lint_results(violation_count)
        return 1 if violation_count > 0 else 0
    
    # Handle check command (lint + tests)
    lint_failed = False
    if parsed_args['action'] == 'check':
        print("🔍 Running comprehensive check (linting + all tests)")
        
        # First run linting
        violation_count = run_lint()
        report_lint_results(violation_count)
        
        # Store lint results for final exit code
        lint_failed = violation_count > 0
        
        print("\n" + "=" * 50)
        print("🧪 Now running all tests...")
        print("=" * 50)
    
    # Extract test parameters
    test_type = parsed_args['test_type']
    modules = parsed_args['modules']
    group = parsed_args['group']
    
    print(f"Command: {parsed_args['command_description']}")
    
    # Show configuration information
    print(f"\n📋 Configuration loaded:")
    print(f"   Test types: {config.get_test_types()}")
    print(f"   Test groups: {list(config.test_groups.keys())}")
    print(f"   Coverage enabled: {config.coverage_enabled}")
    print(f"   HTML coverage: {config.html_coverage}")
    
    # Discover and run tests based on the command
    print(f"\n🔍 Discovering tests...")
    discovered_files = discover_tests(test_type=test_type, modules=modules, group=group, config=config)
    
    if not discovered_files:
        print("❌ No test files found!")
        return 1
    
    print(f"📁 Discovered {len(discovered_files)} test files")
    
    # Discover test methods
    print(f"\n🧪 Discovering test methods...")
    test_methods_by_module = discover_test_methods(discovered_files)
    
    total_methods = sum(len(methods) for methods in test_methods_by_module.values())
    print(f"🎯 Total test methods discovered: {total_methods}")
    
    if total_methods == 0:
        print("❌ No test methods found!")
        return 1
    
    # Run the tests
    print(f"\n🚀 Running tests...")
    test_results, coverage_obj = run_tests(test_methods_by_module, collect_coverage=config.coverage_enabled, config=config)
    
    # Display test summary reporting (Task 6.1)
    report_test_summary(test_results)
    
    # Display detailed test reporting (Task 6.2)
    report_detailed_test_results(test_results)
    
    # Generate coverage report if coverage was collected
    if coverage_obj and config.coverage_enabled:
        coverage_summary = generate_coverage_report(coverage_obj)
        
        # Generate HTML coverage report if enabled
        if config.html_coverage:
            generate_html_coverage_report(coverage_obj, config)
    
    # Show timing breakdown for slowest tests
    if test_results.method_results:
        print(f"\n" + "=" * 60)
        print("⏱️ TIMING BREAKDOWN")
        print("=" * 60)
        # Sort by duration (slowest first)
        sorted_results = sorted(test_results.method_results, key=lambda x: x.duration, reverse=True)
        
        # Show top 5 slowest tests
        top_slow = sorted_results[:5]
        for result in top_slow:
            print(f"   {result.method.full_name}: {result.duration:.3f}s")
    
    # Return appropriate exit code
    if test_results.failed > 0 or test_results.errors > 0 or lint_failed:
        if lint_failed and (test_results.failed > 0 or test_results.errors > 0):
            print(f"\n❌ Both linting and tests failed. Please check above for details.")
        elif lint_failed:
            print(f"\n❌ Linting failed but tests passed. Please fix style violations.")
        else:
            print(f"\n❌ Some tests failed. Please check above for details.")
        return 1
    else:
        print(f"\n✅ All checks passed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())