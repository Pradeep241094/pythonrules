#!/usr/bin/env python3
"""
Unit tests for the testrules.py test runner itself.
This file tests the configuration loading functionality, test discovery mechanisms,
and result collection and reporting.
"""

import unittest
import tempfile
import os
import json
import sys
import shutil
from unittest.mock import Mock, patch, MagicMock

# Import the modules we want to test
import testrules
from testrules import (
    TestMethod, MethodResult, TestResult, Config,
    load_config, discover_tests, discover_test_methods,
    inspect_module_for_tests, safe_import_module,
    get_test_files_by_type, get_all_test_files,
    discover_files_by_modules, resolve_test_group,
    parse_arguments, run_single_test_method
)


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_load_config_with_valid_file(self):
        """Test loading configuration from a valid JSON file."""
        config_data = {
            "test_patterns": {
                "unit": ["test_*.py"],
                "integration": ["integration_*.py"]
            },
            "test_groups": {
                "core": ["test_core"],
                "api": ["test_api"]
            },
            "coverage_enabled": True,
            "html_coverage": False,
            "html_coverage_dir": "custom_htmlcov"
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = load_config(self.config_file)
        
        self.assertIsInstance(config, Config)
        self.assertEqual(config.test_patterns["unit"], ["test_*.py"])
        self.assertEqual(config.test_patterns["integration"], ["integration_*.py"])
        self.assertEqual(config.test_groups["core"], ["test_core"])
        self.assertEqual(config.test_groups["api"], ["test_api"])
        self.assertTrue(config.coverage_enabled)
        self.assertFalse(config.html_coverage)
        self.assertEqual(config.html_coverage_dir, "custom_htmlcov")
    
    def test_load_config_with_missing_file(self):
        """Test loading configuration when file doesn't exist."""
        non_existent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        config = load_config(non_existent_file)
        
        self.assertIsInstance(config, Config)
        # Should use default values
        self.assertIn("unit", config.test_patterns)
        self.assertIn("integration", config.test_patterns)
        self.assertTrue(config.coverage_enabled)
        self.assertTrue(config.html_coverage)
        self.assertEqual(config.html_coverage_dir, "htmlcov")
    
    def test_load_config_with_invalid_json(self):
        """Test loading configuration with invalid JSON."""
        with open(self.config_file, 'w') as f:
            f.write('{"invalid": json content}')
        
        config = load_config(self.config_file)
        
        # Should fall back to defaults
        self.assertIsInstance(config, Config)
        self.assertIn("unit", config.test_patterns)
    
    def test_config_class_initialization(self):
        """Test Config class initialization with various data."""
        # Test with empty data
        config = Config()
        self.assertIsInstance(config.test_patterns, dict)
        self.assertIsInstance(config.test_groups, dict)
        self.assertTrue(config.coverage_enabled)
        
        # Test with custom data
        custom_data = {
            "test_patterns": {"custom": ["custom_*.py"]},
            "coverage_enabled": False
        }
        config = Config(custom_data)
        self.assertEqual(config.test_patterns["custom"], ["custom_*.py"])
        self.assertFalse(config.coverage_enabled)
    
    def test_config_get_test_types(self):
        """Test getting available test types from config."""
        config_data = {
            "test_patterns": {
                "unit": ["test_*.py"],
                "integration": ["integration_*.py"],
                "custom": ["custom_*.py"]
            }
        }
        config = Config(config_data)
        
        test_types = config.get_test_types()
        self.assertIn("unit", test_types)
        self.assertIn("integration", test_types)
        self.assertIn("custom", test_types)
        self.assertEqual(len(test_types), 3)
    
    def test_config_get_patterns_for_test_type(self):
        """Test getting patterns for specific test types."""
        config_data = {
            "test_patterns": {
                "unit": ["test_*.py", "*_test.py"],
                "integration": ["integration_*.py"]
            }
        }
        config = Config(config_data)
        
        unit_patterns = config.get_patterns_for_test_type("unit")
        self.assertEqual(unit_patterns, ["test_*.py", "*_test.py"])
        
        integration_patterns = config.get_patterns_for_test_type("integration")
        self.assertEqual(integration_patterns, ["integration_*.py"])
        
        # Test non-existent type
        nonexistent_patterns = config.get_patterns_for_test_type("nonexistent")
        self.assertEqual(nonexistent_patterns, [])
    
    def test_config_has_test_type(self):
        """Test checking if test type exists in config."""
        config_data = {
            "test_patterns": {
                "unit": ["test_*.py"],
                "integration": ["integration_*.py"]
            }
        }
        config = Config(config_data)
        
        self.assertTrue(config.has_test_type("unit"))
        self.assertTrue(config.has_test_type("integration"))
        self.assertFalse(config.has_test_type("nonexistent"))
    
    def test_config_add_custom_test_type(self):
        """Test adding custom test types to config."""
        config = Config()
        
        config.add_custom_test_type("custom", ["custom_*.py"])
        
        self.assertTrue(config.has_test_type("custom"))
        self.assertEqual(config.get_patterns_for_test_type("custom"), ["custom_*.py"])


class TestTestDiscovery(unittest.TestCase):
    """Test test discovery mechanisms."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content):
        """Helper to create test files."""
        with open(filename, 'w') as f:
            f.write(content)
    
    def test_get_test_files_by_type(self):
        """Test discovering test files by type."""
        # Create test files
        self.create_test_file('test_unit.py', 'import unittest\nclass TestUnit(unittest.TestCase): pass')
        self.create_test_file('integration_test_db.py', 'import unittest\nclass TestDB(unittest.TestCase): pass')
        self.create_test_file('regular_file.py', 'def regular_function(): pass')
        
        config_data = {
            "test_patterns": {
                "unit": ["test_*.py"],
                "integration": ["integration_*.py"]
            }
        }
        config = Config(config_data)
        
        # Test unit file discovery
        unit_files = get_test_files_by_type("unit", config, ".")
        self.assertTrue(any("test_unit.py" in f for f in unit_files))
        self.assertFalse(any("integration_test_db.py" in f for f in unit_files))
        self.assertFalse(any("regular_file.py" in f for f in unit_files))
        
        # Test integration file discovery
        integration_files = get_test_files_by_type("integration", config, ".")
        self.assertTrue(any("integration_test_db.py" in f for f in integration_files))
        self.assertFalse(any("test_unit.py" in f for f in integration_files))
        
        # Test non-existent type
        nonexistent_files = get_test_files_by_type("nonexistent", config, ".")
        self.assertEqual(nonexistent_files, [])
    
    def test_get_all_test_files(self):
        """Test discovering all test files."""
        # Create test files
        self.create_test_file('test_unit.py', 'import unittest\nclass TestUnit(unittest.TestCase): pass')
        self.create_test_file('integration_test_db.py', 'import unittest\nclass TestDB(unittest.TestCase): pass')
        self.create_test_file('e2e_test_workflow.py', 'import unittest\nclass TestWorkflow(unittest.TestCase): pass')
        
        config_data = {
            "test_patterns": {
                "unit": ["test_*.py"],
                "integration": ["integration_*.py"],
                "e2e": ["e2e_*.py"]
            }
        }
        config = Config(config_data)
        
        all_files = get_all_test_files(config, ".")
        
        self.assertIn("unit", all_files)
        self.assertIn("integration", all_files)
        self.assertIn("e2e", all_files)
        
        self.assertTrue(any("test_unit.py" in f for f in all_files["unit"]))
        self.assertTrue(any("integration_test_db.py" in f for f in all_files["integration"]))
        self.assertTrue(any("e2e_test_workflow.py" in f for f in all_files["e2e"]))
    
    def test_discover_files_by_modules(self):
        """Test discovering files by explicit module names."""
        # Create test files
        self.create_test_file('test_module1.py', 'import unittest\nclass TestModule1(unittest.TestCase): pass')
        self.create_test_file('test_module2.py', 'import unittest\nclass TestModule2(unittest.TestCase): pass')
        
        # Test discovering existing modules
        files = discover_files_by_modules(['test_module1', 'test_module2'], ".")
        self.assertTrue(any('test_module1.py' in f for f in files))
        self.assertTrue(any('test_module2.py' in f for f in files))
        
        # Test discovering non-existent module (should not crash)
        files = discover_files_by_modules(['nonexistent_module'], ".")
        self.assertEqual(files, [])
    
    def test_resolve_test_group(self):
        """Test resolving test groups from configuration."""
        config_data = {
            "test_groups": {
                "core": ["test_core1", "test_core2"],
                "api": ["test_api1", "test_api2"],
                "empty": []
            }
        }
        config = Config(config_data)
        
        # Test existing groups
        core_modules = resolve_test_group("core", config)
        self.assertEqual(core_modules, ["test_core1", "test_core2"])
        
        api_modules = resolve_test_group("api", config)
        self.assertEqual(api_modules, ["test_api1", "test_api2"])
        
        # Test empty group
        empty_modules = resolve_test_group("empty", config)
        self.assertEqual(empty_modules, [])
        
        # Test non-existent group
        nonexistent_modules = resolve_test_group("nonexistent", config)
        self.assertEqual(nonexistent_modules, [])
    
    @patch('testrules.get_test_files_by_type')
    @patch('testrules.discover_files_by_modules')
    @patch('testrules.resolve_test_group')
    def test_discover_tests_priority_order(self, mock_resolve_group, mock_discover_modules, mock_get_files):
        """Test that discover_tests follows correct priority order."""
        config = Config()
        
        # Test explicit modules (highest priority)
        mock_discover_modules.return_value = ['module1.py', 'module2.py']
        result = discover_tests(modules=['module1', 'module2'], config=config)
        mock_discover_modules.assert_called_once()
        mock_resolve_group.assert_not_called()
        mock_get_files.assert_not_called()
        
        # Reset mocks
        mock_discover_modules.reset_mock()
        mock_resolve_group.reset_mock()
        mock_get_files.reset_mock()
        
        # Test group (second priority)
        mock_resolve_group.return_value = ['group_module1', 'group_module2']
        mock_discover_modules.return_value = ['group_module1.py', 'group_module2.py']
        result = discover_tests(group='test_group', config=config)
        mock_resolve_group.assert_called_once_with('test_group', config)
        mock_discover_modules.assert_called_once()
        mock_get_files.assert_not_called()
        
        # Reset mocks
        mock_discover_modules.reset_mock()
        mock_resolve_group.reset_mock()
        mock_get_files.reset_mock()
        
        # Test test type (third priority)
        mock_get_files.return_value = ['unit_test1.py', 'unit_test2.py']
        result = discover_tests(test_type='unit', config=config)
        mock_get_files.assert_called_once_with('unit', config, '.')
        mock_resolve_group.assert_not_called()
        mock_discover_modules.assert_not_called()


class TestModuleInspection(unittest.TestCase):
    """Test module inspection for test methods."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content):
        """Helper to create test files."""
        with open(filename, 'w') as f:
            f.write(content)
    
    def test_safe_import_module_success(self):
        """Test successful module import."""
        content = '''
import unittest

class TestSample(unittest.TestCase):
    def test_method(self):
        self.assertTrue(True)
'''
        self.create_test_file('test_sample.py', content)
        
        module, success, error = safe_import_module('test_sample', 'test_sample.py')
        
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertIsNotNone(module)
        self.assertTrue(hasattr(module, 'TestSample'))
    
    def test_safe_import_module_syntax_error(self):
        """Test module import with syntax error."""
        content = '''
import unittest

class TestSample(unittest.TestCase):
    def test_method(self):
        self.assertTrue(True
        # Missing closing parenthesis
'''
        self.create_test_file('test_syntax_error.py', content)
        
        module, success, error = safe_import_module('test_syntax_error', 'test_syntax_error.py')
        
        self.assertFalse(success)
        self.assertIsNone(module)
        self.assertIsNotNone(error)
        self.assertIn('SyntaxError', error)
    
    def test_safe_import_module_import_error(self):
        """Test module import with import error."""
        content = '''
import nonexistent_module
import unittest

class TestSample(unittest.TestCase):
    def test_method(self):
        self.assertTrue(True)
'''
        self.create_test_file('test_import_error.py', content)
        
        module, success, error = safe_import_module('test_import_error', 'test_import_error.py')
        
        self.assertFalse(success)
        self.assertIsNone(module)
        self.assertIsNotNone(error)
        self.assertIn('ImportError', error)
    
    def test_inspect_module_for_tests_with_class_methods(self):
        """Test inspecting module with unittest.TestCase classes."""
        content = '''
import unittest

class TestSample(unittest.TestCase):
    def test_method1(self):
        self.assertTrue(True)
    
    def test_method2(self):
        self.assertEqual(1, 1)
    
    def helper_method(self):
        # This should not be discovered
        pass

class RegularClass:
    def test_method(self):
        # This should not be discovered (not a TestCase)
        pass
'''
        self.create_test_file('test_class_methods.py', content)
        
        test_methods = inspect_module_for_tests('test_class_methods', 'test_class_methods.py')
        
        self.assertEqual(len(test_methods), 2)
        
        method_names = [method.name for method in test_methods]
        self.assertIn('test_method1', method_names)
        self.assertIn('test_method2', method_names)
        self.assertNotIn('helper_method', method_names)
        
        # Check method details
        for method in test_methods:
            self.assertEqual(method.module, 'test_class_methods')
            self.assertEqual(method.class_name, 'TestSample')
            self.assertEqual(method.file_path, 'test_class_methods.py')
    
    def test_inspect_module_for_tests_with_standalone_functions(self):
        """Test inspecting module with standalone test functions."""
        content = '''
import unittest

def test_standalone_function1():
    assert True

def test_standalone_function2():
    assert 1 == 1

def regular_function():
    # This should not be discovered
    pass

class TestSample(unittest.TestCase):
    def test_class_method(self):
        self.assertTrue(True)
'''
        self.create_test_file('test_standalone.py', content)
        
        test_methods = inspect_module_for_tests('test_standalone', 'test_standalone.py')
        
        # Should find both standalone functions and class method
        self.assertEqual(len(test_methods), 3)
        
        method_names = [method.name for method in test_methods]
        self.assertIn('test_standalone_function1', method_names)
        self.assertIn('test_standalone_function2', method_names)
        self.assertIn('test_class_method', method_names)
        self.assertNotIn('regular_function', method_names)
        
        # Check standalone function details
        standalone_methods = [m for m in test_methods if m.class_name is None]
        self.assertEqual(len(standalone_methods), 2)
        
        for method in standalone_methods:
            self.assertEqual(method.module, 'test_standalone')
            self.assertIsNone(method.class_name)
    
    def test_inspect_module_for_tests_import_failure(self):
        """Test inspecting module that fails to import."""
        # Don't create the file, so import will fail
        test_methods = inspect_module_for_tests('nonexistent_module', 'nonexistent.py')
        
        self.assertEqual(test_methods, [])
    
    def test_discover_test_methods(self):
        """Test discovering test methods from multiple files."""
        # Create multiple test files
        content1 = '''
import unittest

class TestFile1(unittest.TestCase):
    def test_method1(self):
        self.assertTrue(True)
    
    def test_method2(self):
        self.assertEqual(1, 1)
'''
        
        content2 = '''
import unittest

class TestFile2(unittest.TestCase):
    def test_method3(self):
        self.assertTrue(True)

def test_standalone():
    assert True
'''
        
        self.create_test_file('test_file1.py', content1)
        self.create_test_file('test_file2.py', content2)
        
        test_files = ['test_file1.py', 'test_file2.py']
        test_methods_by_module = discover_test_methods(test_files)
        
        self.assertIn('test_file1', test_methods_by_module)
        self.assertIn('test_file2', test_methods_by_module)
        
        # Check test_file1 methods
        file1_methods = test_methods_by_module['test_file1']
        self.assertEqual(len(file1_methods), 2)
        method_names = [method.name for method in file1_methods]
        self.assertIn('test_method1', method_names)
        self.assertIn('test_method2', method_names)
        
        # Check test_file2 methods
        file2_methods = test_methods_by_module['test_file2']
        self.assertEqual(len(file2_methods), 2)
        method_names = [method.name for method in file2_methods]
        self.assertIn('test_method3', method_names)
        self.assertIn('test_standalone', method_names)


class TestDataModels(unittest.TestCase):
    """Test data model classes."""
    
    def test_test_method_creation(self):
        """Test TestMethod object creation and properties."""
        method = TestMethod(
            name='test_example',
            module='test_module',
            class_name='TestClass',
            file_path='/path/to/test_module.py'
        )
        
        self.assertEqual(method.name, 'test_example')
        self.assertEqual(method.module, 'test_module')
        self.assertEqual(method.class_name, 'TestClass')
        self.assertEqual(method.file_path, '/path/to/test_module.py')
        self.assertEqual(method.full_name, 'test_module.TestClass.test_example')
        
        # Test string representations
        self.assertEqual(str(method), 'test_module.TestClass.test_example')
        self.assertIn('test_example', repr(method))
        self.assertIn('test_module', repr(method))
        self.assertIn('TestClass', repr(method))
    
    def test_test_method_without_class(self):
        """Test TestMethod for standalone functions."""
        method = TestMethod(
            name='test_standalone',
            module='test_module',
            class_name=None,
            file_path='/path/to/test_module.py'
        )
        
        self.assertEqual(method.full_name, 'test_module.test_standalone')
        self.assertIsNone(method.class_name)
    
    def test_method_result_creation(self):
        """Test MethodResult object creation and properties."""
        method = TestMethod('test_example', 'test_module', 'TestClass')
        result = MethodResult(
            method=method,
            status='pass',
            duration=0.123,
            error=None,
            traceback_str=None
        )
        
        self.assertEqual(result.method, method)
        self.assertEqual(result.status, 'pass')
        self.assertEqual(result.duration, 0.123)
        self.assertIsNone(result.error)
        self.assertIsNone(result.traceback_str)
        
        # Test string representations
        self.assertIn('PASS', str(result))
        self.assertIn('test_module.TestClass.test_example', str(result))
        self.assertIn('pass', repr(result))
        self.assertIn('0.123', repr(result))
    
    def test_method_result_with_error(self):
        """Test MethodResult with error information."""
        method = TestMethod('test_example', 'test_module', 'TestClass')
        result = MethodResult(
            method=method,
            status='fail',
            duration=0.456,
            error='AssertionError: 1 != 2',
            traceback_str='Traceback (most recent call last):\n  File "test.py", line 1, in test\n    assert 1 == 2\nAssertionError: 1 != 2'
        )
        
        self.assertEqual(result.status, 'fail')
        self.assertEqual(result.error, 'AssertionError: 1 != 2')
        self.assertIsNotNone(result.traceback_str)
        self.assertIn('FAIL', str(result))
    
    def test_test_result_creation_and_methods(self):
        """Test TestResult object creation and methods."""
        test_result = TestResult()
        
        # Initial state
        self.assertEqual(test_result.total, 0)
        self.assertEqual(test_result.passed, 0)
        self.assertEqual(test_result.failed, 0)
        self.assertEqual(test_result.errors, 0)
        self.assertEqual(test_result.method_results, [])
        self.assertEqual(test_result.duration, 0.0)
        self.assertIsNone(test_result.start_time)
        self.assertIsNone(test_result.end_time)
    
    def test_test_result_add_results(self):
        """Test adding method results to TestResult."""
        test_result = TestResult()
        
        # Create test methods and results
        method1 = TestMethod('test1', 'module', 'TestClass')
        method2 = TestMethod('test2', 'module', 'TestClass')
        method3 = TestMethod('test3', 'module', 'TestClass')
        
        result1 = MethodResult(method1, 'pass', 0.1)
        result2 = MethodResult(method2, 'fail', 0.2, 'AssertionError')
        result3 = MethodResult(method3, 'error', 0.3, 'ValueError')
        
        # Add results
        test_result.add_result(result1)
        test_result.add_result(result2)
        test_result.add_result(result3)
        
        # Check counts
        self.assertEqual(test_result.total, 3)
        self.assertEqual(test_result.passed, 1)
        self.assertEqual(test_result.failed, 1)
        self.assertEqual(test_result.errors, 1)
        self.assertEqual(len(test_result.method_results), 3)
    
    def test_test_result_success_rate(self):
        """Test success rate calculation."""
        test_result = TestResult()
        
        # Test with no results
        self.assertEqual(test_result.get_success_rate(), 0.0)
        
        # Add some results
        method1 = TestMethod('test1', 'module', 'TestClass')
        method2 = TestMethod('test2', 'module', 'TestClass')
        method3 = TestMethod('test3', 'module', 'TestClass')
        method4 = TestMethod('test4', 'module', 'TestClass')
        
        test_result.add_result(MethodResult(method1, 'pass', 0.1))
        test_result.add_result(MethodResult(method2, 'pass', 0.1))
        test_result.add_result(MethodResult(method3, 'pass', 0.1))
        test_result.add_result(MethodResult(method4, 'fail', 0.1))
        
        # 3 out of 4 passed = 75%
        self.assertEqual(test_result.get_success_rate(), 75.0)
    
    def test_test_result_get_failed_results(self):
        """Test getting failed and error results."""
        test_result = TestResult()
        
        # Create test methods and results
        method1 = TestMethod('test1', 'module', 'TestClass')
        method2 = TestMethod('test2', 'module', 'TestClass')
        method3 = TestMethod('test3', 'module', 'TestClass')
        method4 = TestMethod('test4', 'module', 'TestClass')
        
        result1 = MethodResult(method1, 'pass', 0.1)
        result2 = MethodResult(method2, 'fail', 0.2, 'AssertionError')
        result3 = MethodResult(method3, 'error', 0.3, 'ValueError')
        result4 = MethodResult(method4, 'pass', 0.1)
        
        test_result.add_result(result1)
        test_result.add_result(result2)
        test_result.add_result(result3)
        test_result.add_result(result4)
        
        failed_results = test_result.get_failed_results()
        
        self.assertEqual(len(failed_results), 2)
        statuses = [result.status for result in failed_results]
        self.assertIn('fail', statuses)
        self.assertIn('error', statuses)
        self.assertNotIn('pass', statuses)
    
    def test_test_result_timing(self):
        """Test timing functionality."""
        test_result = TestResult()
        
        # Test timing
        test_result.start_timing()
        self.assertIsNotNone(test_result.start_time)
        
        # Simulate some time passing
        import time
        time.sleep(0.01)  # 10ms
        
        test_result.stop_timing()
        self.assertIsNotNone(test_result.end_time)
        self.assertGreater(test_result.duration, 0)
        self.assertGreater(test_result.end_time, test_result.start_time)


class TestArgumentParsing(unittest.TestCase):
    """Test command-line argument parsing."""
    
    def setUp(self):
        """Set up test configuration."""
        self.config_data = {
            "test_patterns": {
                "unit": ["test_*.py"],
                "integration": ["integration_*.py"],
                "e2e": ["e2e_*.py"]
            },
            "test_groups": {
                "core": ["test_core1", "test_core2"],
                "api": ["test_api1", "test_api2"]
            }
        }
        self.config = Config(self.config_data)
    
    def test_parse_arguments_no_args(self):
        """Test parsing with no arguments."""
        result = parse_arguments([], self.config)
        
        self.assertEqual(result['action'], 'test')
        self.assertIsNone(result['test_type'])
        self.assertIsNone(result['modules'])
        self.assertIsNone(result['group'])
        self.assertEqual(result['command_description'], 'all tests')
    
    def test_parse_arguments_help(self):
        """Test parsing help commands."""
        for help_arg in ['help', '--help', '-h']:
            result = parse_arguments([help_arg], self.config)
            
            self.assertEqual(result['action'], 'help')
            self.assertIsNone(result['test_type'])
            self.assertIsNone(result['modules'])
            self.assertIsNone(result['group'])
            self.assertEqual(result['command_description'], 'help')
    
    def test_parse_arguments_special_commands(self):
        """Test parsing special commands."""
        # Test lint command
        result = parse_arguments(['lint'], self.config)
        self.assertEqual(result['action'], 'lint')
        self.assertEqual(result['command_description'], 'linting only')
        
        # Test check command
        result = parse_arguments(['check'], self.config)
        self.assertEqual(result['action'], 'check')
        self.assertEqual(result['command_description'], 'comprehensive check (linting + all tests)')
    
    def test_parse_arguments_test_types(self):
        """Test parsing test type commands."""
        for test_type in ['unit', 'integration', 'e2e']:
            result = parse_arguments([test_type], self.config)
            
            self.assertEqual(result['action'], 'test')
            self.assertEqual(result['test_type'], test_type)
            self.assertIsNone(result['modules'])
            self.assertIsNone(result['group'])
            self.assertEqual(result['command_description'], f'{test_type} tests')
    
    def test_parse_arguments_test_groups(self):
        """Test parsing test group commands."""
        for group in ['core', 'api']:
            result = parse_arguments([group], self.config)
            
            self.assertEqual(result['action'], 'test')
            self.assertIsNone(result['test_type'])
            self.assertIsNone(result['modules'])
            self.assertEqual(result['group'], group)
            self.assertEqual(result['command_description'], f'test group "{group}"')
    
    def test_parse_arguments_single_module(self):
        """Test parsing single module command."""
        result = parse_arguments(['test_module'], self.config)
        
        self.assertEqual(result['action'], 'test')
        self.assertIsNone(result['test_type'])
        self.assertEqual(result['modules'], ['test_module'])
        self.assertIsNone(result['group'])
        self.assertEqual(result['command_description'], 'module "test_module"')
    
    def test_parse_arguments_multiple_modules(self):
        """Test parsing multiple module commands."""
        result = parse_arguments(['module1', 'module2', 'module3'], self.config)
        
        self.assertEqual(result['action'], 'test')
        self.assertIsNone(result['test_type'])
        self.assertEqual(result['modules'], ['module1', 'module2', 'module3'])
        self.assertIsNone(result['group'])
        self.assertEqual(result['command_description'], 'modules: module1, module2, module3')


class TestTestExecution(unittest.TestCase):
    """Test test execution functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename, content):
        """Helper to create test files."""
        with open(filename, 'w') as f:
            f.write(content)
    
    def test_run_single_test_method_pass(self):
        """Test running a single test method that passes."""
        content = '''
import unittest

class TestSample(unittest.TestCase):
    def test_pass(self):
        self.assertTrue(True)
'''
        self.create_test_file('test_pass.py', content)
        
        method = TestMethod('test_pass', 'test_pass', 'TestSample', 'test_pass.py')
        result = run_single_test_method(method)
        
        self.assertEqual(result.status, 'pass')
        self.assertIsNone(result.error)
        self.assertIsNone(result.traceback_str)
        self.assertGreater(result.duration, 0)
    
    def test_run_single_test_method_fail(self):
        """Test running a single test method that fails."""
        content = '''
import unittest

class TestSample(unittest.TestCase):
    def test_fail(self):
        self.assertEqual(1, 2)
'''
        self.create_test_file('test_fail.py', content)
        
        method = TestMethod('test_fail', 'test_fail', 'TestSample', 'test_fail.py')
        result = run_single_test_method(method)
        
        self.assertEqual(result.status, 'fail')
        self.assertIsNotNone(result.error)
        self.assertIn('1 != 2', str(result.error))
        self.assertGreater(result.duration, 0)
    
    def test_run_single_test_method_error(self):
        """Test running a single test method that has an error."""
        content = '''
import unittest

class TestSample(unittest.TestCase):
    def test_error(self):
        raise ValueError("Test error")
'''
        self.create_test_file('test_error.py', content)
        
        method = TestMethod('test_error', 'test_error', 'TestSample', 'test_error.py')
        result = run_single_test_method(method)
        
        self.assertEqual(result.status, 'error')
        self.assertIsNotNone(result.error)
        self.assertIn('Test error', str(result.error))
        self.assertGreater(result.duration, 0)
    
    def test_run_single_test_method_standalone_function(self):
        """Test running a standalone test function."""
        content = '''
def test_standalone():
    assert True
'''
        self.create_test_file('test_standalone.py', content)
        
        method = TestMethod('test_standalone', 'test_standalone', None, 'test_standalone.py')
        result = run_single_test_method(method)
        
        self.assertEqual(result.status, 'pass')
        self.assertIsNone(result.error)
        self.assertGreater(result.duration, 0)
    
    def test_run_single_test_method_import_error(self):
        """Test running a test method from a module that can't be imported."""
        # Don't create the file, so import will fail
        method = TestMethod('test_method', 'nonexistent', 'TestClass', 'nonexistent.py')
        result = run_single_test_method(method)
        
        self.assertEqual(result.status, 'error')
        self.assertIsNotNone(result.error)
        self.assertIn('Failed to import module', result.error)


if __name__ == '__main__':
    unittest.main()