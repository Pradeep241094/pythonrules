#!/usr/bin/env python3
"""
Test discovery functionality for the lightweight test runner.
"""

import os
import sys
import glob
import unittest
import importlib
import importlib.util
from typing import Dict, List, Optional

from .core import TestMethod


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
        from .core import Config
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