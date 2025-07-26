#!/usr/bin/env python3
"""
Test execution functionality for the lightweight test runner.
"""

import time
import unittest
import traceback

from .core import MethodResult, TestResult
from .discovery import safe_import_module

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False


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
        # Get coverage configuration
        coverage_config = config.coverage_config
        
        # Initialize coverage with configuration
        cov = coverage.Coverage(
            branch=True,  # Enable branch coverage
            source=coverage_config.get('source', ['.']),
            omit=coverage_config.get('omit', [
                '*/tests/*',
                '*/test_*',
                '*_test.py',
                'setup.py',
                '*/venv/*',
                '*/env/*',
                '*/.venv/*',
            ]),
            include=coverage_config.get('include', ['*.py'])
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
            from .core import Config
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