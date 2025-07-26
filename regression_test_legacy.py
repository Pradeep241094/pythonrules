#!/usr/bin/env python3
"""
Regression tests to ensure existing functionality continues to work.
These tests verify that changes don't break previously working features.
"""

import unittest
import tempfile
import os
import json


class LegacyCalculator:
    """Legacy calculator implementation that we need to maintain compatibility with."""
    
    def __init__(self):
        """Initialize calculator with legacy behavior."""
        self.history = []
        self.precision = 2  # Legacy precision setting
    
    def add(self, a, b):
        """Add two numbers with legacy rounding."""
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a, b):
        """Subtract two numbers with legacy rounding."""
        result = round(a - b, self.precision)
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a, b):
        """Multiply two numbers with legacy rounding."""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a, b):
        """Divide two numbers with legacy error handling."""
        if b == 0:
            # Legacy behavior: return string instead of raising exception
            result = "ERROR: Division by zero"
            self.history.append(f"{a} / {b} = {result}")
            return result
        
        result = round(a / b, self.precision)
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history."""
        self.history.clear()


class LegacyFileProcessor:
    """Legacy file processor that handles old file formats."""
    
    @staticmethod
    def process_legacy_config(file_path):
        """Process legacy configuration files."""
        if not os.path.exists(file_path):
            return {"error": "File not found"}
        
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
            
            # Legacy format: key=value pairs separated by newlines
            config = {}
            for line in content.split('\n'):
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    # Legacy behavior: convert numeric strings to numbers
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass  # Keep as string
                    config[key.strip()] = value
            
            return config
        
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def convert_to_json(legacy_config):
        """Convert legacy config to JSON format."""
        if "error" in legacy_config:
            return legacy_config
        
        # Legacy conversion rules
        converted = {}
        for key, value in legacy_config.items():
            # Legacy behavior: uppercase all keys
            new_key = key.upper()
            converted[new_key] = value
        
        return converted


class TestLegacyCalculatorRegression(unittest.TestCase):
    """Regression tests for legacy calculator functionality."""
    
    def setUp(self):
        """Set up test calculator."""
        self.calc = LegacyCalculator()
    
    def test_legacy_addition_precision(self):
        """Test that addition maintains legacy precision behavior."""
        result = self.calc.add(1.234, 2.567)
        self.assertEqual(result, 3.8)  # Should round to 2 decimal places
    
    def test_legacy_subtraction_precision(self):
        """Test that subtraction maintains legacy precision behavior."""
        result = self.calc.subtract(5.789, 2.123)
        self.assertEqual(result, 3.67)  # Should round to 2 decimal places
    
    def test_legacy_multiplication_precision(self):
        """Test that multiplication maintains legacy precision behavior."""
        result = self.calc.multiply(3.333, 2.222)
        self.assertEqual(result, 7.41)  # Should round to 2 decimal places
    
    def test_legacy_division_by_zero_behavior(self):
        """Test that division by zero maintains legacy string return behavior."""
        result = self.calc.divide(10, 0)
        self.assertEqual(result, "ERROR: Division by zero")
        # Verify it doesn't raise an exception (legacy behavior)
    
    def test_legacy_division_precision(self):
        """Test that division maintains legacy precision behavior."""
        result = self.calc.divide(10, 3)
        self.assertEqual(result, 3.33)  # Should round to 2 decimal places
    
    def test_legacy_history_tracking(self):
        """Test that history tracking works as expected."""
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        self.calc.multiply(2, 4)
        
        history = self.calc.get_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0], "1 + 2 = 3")
        self.assertEqual(history[1], "5 - 3 = 2")
        self.assertEqual(history[2], "2 * 4 = 8")
    
    def test_legacy_history_clear(self):
        """Test that history clearing works correctly."""
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        self.assertEqual(len(self.calc.get_history()), 2)
        
        self.calc.clear_history()
        self.assertEqual(len(self.calc.get_history()), 0)
    
    def test_legacy_division_by_zero_in_history(self):
        """Test that division by zero is recorded correctly in history."""
        self.calc.divide(10, 0)
        history = self.calc.get_history()
        self.assertEqual(history[0], "10 / 0 = ERROR: Division by zero")


class TestLegacyFileProcessorRegression(unittest.TestCase):
    """Regression tests for legacy file processor."""
    
    def setUp(self):
        """Set up test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_legacy_config_file_parsing(self):
        """Test that legacy config files are parsed correctly."""
        config_content = """# Legacy config file
name=TestApp
version=1.0
port=8080
debug=true
timeout=30.5
# This is a comment
description=A test application"""
        
        config_file = os.path.join(self.temp_dir, 'legacy.conf')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        result = LegacyFileProcessor.process_legacy_config(config_file)
        
        expected = {
            'name': 'TestApp',
            'version': 1.0,  # The legacy processor converts numeric strings to numbers
            'port': 8080,
            'debug': 'true',
            'timeout': 30.5,
            'description': 'A test application'
        }
        
        self.assertEqual(result, expected)
    
    def test_legacy_config_numeric_conversion(self):
        """Test that numeric values are converted correctly."""
        config_content = """integer_value=42
float_value=3.14159
string_value=hello
zero_value=0
negative_value=-10"""
        
        config_file = os.path.join(self.temp_dir, 'numeric.conf')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        result = LegacyFileProcessor.process_legacy_config(config_file)
        
        self.assertEqual(result['integer_value'], 42)
        self.assertEqual(result['float_value'], 3.14159)
        self.assertEqual(result['string_value'], 'hello')
        self.assertEqual(result['zero_value'], 0)
        self.assertEqual(result['negative_value'], -10)
    
    def test_legacy_config_missing_file(self):
        """Test handling of missing config files."""
        result = LegacyFileProcessor.process_legacy_config('nonexistent.conf')
        self.assertEqual(result, {"error": "File not found"})
    
    def test_legacy_to_json_conversion(self):
        """Test conversion from legacy format to JSON."""
        legacy_config = {
            'name': 'TestApp',
            'port': 8080,
            'debug': 'true'
        }
        
        result = LegacyFileProcessor.convert_to_json(legacy_config)
        
        expected = {
            'NAME': 'TestApp',
            'PORT': 8080,
            'DEBUG': 'true'
        }
        
        self.assertEqual(result, expected)
    
    def test_legacy_to_json_with_error(self):
        """Test that errors are passed through in conversion."""
        legacy_config = {"error": "File not found"}
        result = LegacyFileProcessor.convert_to_json(legacy_config)
        self.assertEqual(result, {"error": "File not found"})
    
    def test_legacy_config_with_equals_in_value(self):
        """Test handling of equals signs in values."""
        config_content = """url=http://example.com/path?param=value
equation=x=y+z
simple=test"""
        
        config_file = os.path.join(self.temp_dir, 'equals.conf')
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        result = LegacyFileProcessor.process_legacy_config(config_file)
        
        self.assertEqual(result['url'], 'http://example.com/path?param=value')
        self.assertEqual(result['equation'], 'x=y+z')
        self.assertEqual(result['simple'], 'test')


class TestBackwardCompatibilityRegression(unittest.TestCase):
    """Tests to ensure backward compatibility is maintained."""
    
    def test_calculator_and_processor_integration(self):
        """Test that calculator and processor work together as before."""
        # Create a config file for calculator settings
        config_content = """precision=3
history_enabled=true
max_history=100"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write(config_content)
            config_file = f.name
        
        try:
            # Process config
            config = LegacyFileProcessor.process_legacy_config(config_file)
            
            # Use config with calculator (simulating legacy integration)
            calc = LegacyCalculator()
            if 'precision' in config:
                calc.precision = config['precision']
            
            # Test calculation with new precision
            result = calc.add(1.23456, 2.34567)
            self.assertEqual(result, 3.580)  # Should use precision=3
            
        finally:
            os.unlink(config_file)
    
    def test_legacy_error_handling_patterns(self):
        """Test that legacy error handling patterns are preserved."""
        calc = LegacyCalculator()
        
        # Test that division by zero returns string (not exception)
        result = calc.divide(1, 0)
        self.assertIsInstance(result, str)
        self.assertIn("ERROR", result)
        
        # Test that other operations still work after error
        result2 = calc.add(1, 2)
        self.assertEqual(result2, 3)
        
        # Test that error is in history
        history = calc.get_history()
        self.assertTrue(any("ERROR" in entry for entry in history))
    
    def test_legacy_data_format_compatibility(self):
        """Test that legacy data formats are still supported."""
        # Test empty config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("")
            empty_config_file = f.name
        
        try:
            result = LegacyFileProcessor.process_legacy_config(empty_config_file)
            self.assertEqual(result, {})  # Should return empty dict, not error
        finally:
            os.unlink(empty_config_file)
        
        # Test config with only comments
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
            f.write("# Only comments\n# Another comment\n")
            comment_config_file = f.name
        
        try:
            result = LegacyFileProcessor.process_legacy_config(comment_config_file)
            self.assertEqual(result, {})  # Should return empty dict
        finally:
            os.unlink(comment_config_file)


if __name__ == '__main__':
    unittest.main()