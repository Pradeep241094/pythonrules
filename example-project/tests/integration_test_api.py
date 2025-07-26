#!/usr/bin/env python3
"""
Integration tests for API-like functionality.
"""

import unittest
import tempfile
import os
import sys

# Add src directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calculator import Calculator
from utils import save_to_file, load_from_file, format_number


class TestCalculatorWithFileStorage(unittest.TestCase):
    """Integration tests for calculator with file storage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.calc = Calculator()
        self.history_file = os.path.join(self.temp_dir, 'calc_history.json')
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.history_file):
            os.unlink(self.history_file)
        os.rmdir(self.temp_dir)
    
    def test_calculator_with_persistent_history(self):
        """Test calculator operations with persistent history storage."""
        # Perform some calculations
        self.calc.add(10, 5)
        self.calc.multiply(3, 4)
        self.calc.divide(20, 4)
        
        # Save history to file
        history_data = {
            'operations': self.calc.get_history(),
            'total_operations': len(self.calc.get_history())
        }
        save_to_file(history_data, self.history_file)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(self.history_file))
        
        # Load and verify data
        loaded_data = load_from_file(self.history_file)
        self.assertEqual(loaded_data['total_operations'], 3)
        self.assertEqual(len(loaded_data['operations']), 3)
        self.assertIn('10 + 5 = 15', loaded_data['operations'])
        self.assertIn('3 * 4 = 12', loaded_data['operations'])
        self.assertIn('20 / 4 = 5.0', loaded_data['operations'])
    
    def test_calculator_results_formatting(self):
        """Test calculator results with number formatting."""
        # Perform calculations that result in decimals
        result1 = self.calc.divide(10, 3)
        result2 = self.calc.divide(22, 7)
        
        # Format results
        formatted_result1 = format_number(result1, 2)
        formatted_result2 = format_number(result2, 3)
        
        # Verify formatting
        self.assertEqual(formatted_result1, 3.33)
        self.assertEqual(formatted_result2, 3.143)
        
        # Save formatted results
        results_data = {
            'raw_results': [result1, result2],
            'formatted_results': [formatted_result1, formatted_result2],
            'precision_used': [2, 3]
        }
        
        results_file = os.path.join(self.temp_dir, 'formatted_results.json')
        save_to_file(results_data, results_file)
        
        # Verify saved data
        loaded_results = load_from_file(results_file)
        self.assertEqual(len(loaded_results['raw_results']), 2)
        self.assertEqual(len(loaded_results['formatted_results']), 2)
        self.assertEqual(loaded_results['formatted_results'][0], 3.33)
        self.assertEqual(loaded_results['formatted_results'][1], 3.143)
        
        # Clean up
        os.unlink(results_file)
    
    def test_calculator_batch_operations(self):
        """Test calculator with batch operations and file I/O."""
        # Define batch operations
        operations = [
            ('add', 10, 5),
            ('subtract', 20, 8),
            ('multiply', 6, 7),
            ('divide', 100, 4),
            ('add', 15, 25)
        ]
        
        results = []
        
        # Execute batch operations
        for operation, a, b in operations:
            if operation == 'add':
                result = self.calc.add(a, b)
            elif operation == 'subtract':
                result = self.calc.subtract(a, b)
            elif operation == 'multiply':
                result = self.calc.multiply(a, b)
            elif operation == 'divide':
                result = self.calc.divide(a, b)
            
            results.append({
                'operation': operation,
                'operands': [a, b],
                'result': result
            })
        
        # Save batch results
        batch_data = {
            'total_operations': len(operations),
            'results': results,
            'history': self.calc.get_history()
        }
        
        batch_file = os.path.join(self.temp_dir, 'batch_results.json')
        save_to_file(batch_data, batch_file)
        
        # Verify batch results
        loaded_batch = load_from_file(batch_file)
        self.assertEqual(loaded_batch['total_operations'], 5)
        self.assertEqual(len(loaded_batch['results']), 5)
        self.assertEqual(len(loaded_batch['history']), 5)
        
        # Verify specific results
        self.assertEqual(loaded_batch['results'][0]['result'], 15)  # 10 + 5
        self.assertEqual(loaded_batch['results'][1]['result'], 12)  # 20 - 8
        self.assertEqual(loaded_batch['results'][2]['result'], 42)  # 6 * 7
        self.assertEqual(loaded_batch['results'][3]['result'], 25.0)  # 100 / 4
        self.assertEqual(loaded_batch['results'][4]['result'], 40)  # 15 + 25
        
        # Clean up
        os.unlink(batch_file)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling across modules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.calc = Calculator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any remaining files
        for file in os.listdir(self.temp_dir):
            os.unlink(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_division_by_zero_with_error_logging(self):
        """Test division by zero error with error logging to file."""
        error_log = []
        
        try:
            self.calc.divide(10, 0)
        except ValueError as e:
            error_log.append({
                'error_type': 'ValueError',
                'error_message': str(e),
                'operation': 'divide',
                'operands': [10, 0]
            })
        
        # Save error log
        error_file = os.path.join(self.temp_dir, 'error_log.json')
        save_to_file({'errors': error_log}, error_file)
        
        # Verify error was logged
        loaded_errors = load_from_file(error_file)
        self.assertEqual(len(loaded_errors['errors']), 1)
        self.assertEqual(loaded_errors['errors'][0]['error_type'], 'ValueError')
        self.assertEqual(loaded_errors['errors'][0]['error_message'], 'Cannot divide by zero')
    
    def test_file_not_found_error_handling(self):
        """Test file not found error handling."""
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        
        error_occurred = False
        error_message = ""
        
        try:
            load_from_file(nonexistent_file)
        except FileNotFoundError as e:
            error_occurred = True
            error_message = str(e)
        
        self.assertTrue(error_occurred)
        self.assertIn('not found', error_message)


if __name__ == '__main__':
    unittest.main()