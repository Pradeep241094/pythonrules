#!/usr/bin/env python3
"""
Integration tests for database operations.
These tests verify that multiple components work together correctly.
"""

import unittest
import tempfile
import os
import json


class SimpleDatabase:
    """Simple file-based database for demonstration."""
    
    def __init__(self, db_path):
        """Initialize database with file path."""
        self.db_path = db_path
        self.data = {}
        self.load()
    
    def load(self):
        """Load data from file."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.data = {}
    
    def save(self):
        """Save data to file."""
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def create(self, key, value):
        """Create a new record."""
        if key in self.data:
            raise ValueError(f"Key '{key}' already exists")
        self.data[key] = value
        self.save()
    
    def read(self, key):
        """Read a record."""
        if key not in self.data:
            raise KeyError(f"Key '{key}' not found")
        return self.data[key]
    
    def update(self, key, value):
        """Update an existing record."""
        if key not in self.data:
            raise KeyError(f"Key '{key}' not found")
        self.data[key] = value
        self.save()
    
    def delete(self, key):
        """Delete a record."""
        if key not in self.data:
            raise KeyError(f"Key '{key}' not found")
        del self.data[key]
        self.save()
    
    def list_all(self):
        """List all records."""
        return dict(self.data)


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.db = SimpleDatabase(self.temp_file.name)
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_create_and_read_record(self):
        """Test creating and reading a record."""
        self.db.create('user1', {'name': 'John', 'age': 30})
        result = self.db.read('user1')
        self.assertEqual(result, {'name': 'John', 'age': 30})
    
    def test_create_update_read_workflow(self):
        """Test complete CRUD workflow."""
        # Create
        self.db.create('user2', {'name': 'Jane', 'age': 25})
        
        # Read
        result = self.db.read('user2')
        self.assertEqual(result['name'], 'Jane')
        
        # Update
        self.db.update('user2', {'name': 'Jane Smith', 'age': 26})
        updated_result = self.db.read('user2')
        self.assertEqual(updated_result['name'], 'Jane Smith')
        self.assertEqual(updated_result['age'], 26)
        
        # Delete
        self.db.delete('user2')
        with self.assertRaises(KeyError):
            self.db.read('user2')
    
    def test_persistence_across_instances(self):
        """Test that data persists across database instances."""
        # Create data with first instance
        self.db.create('persistent_user', {'name': 'Bob', 'age': 35})
        
        # Create new instance pointing to same file
        db2 = SimpleDatabase(self.temp_file.name)
        result = db2.read('persistent_user')
        self.assertEqual(result, {'name': 'Bob', 'age': 35})
    
    def test_multiple_operations_consistency(self):
        """Test consistency across multiple operations."""
        # Add multiple records
        users = [
            ('user1', {'name': 'Alice', 'age': 28}),
            ('user2', {'name': 'Bob', 'age': 32}),
            ('user3', {'name': 'Charlie', 'age': 24})
        ]
        
        for key, value in users:
            self.db.create(key, value)
        
        # Verify all records exist
        all_data = self.db.list_all()
        self.assertEqual(len(all_data), 3)
        
        # Update one record
        self.db.update('user2', {'name': 'Robert', 'age': 33})
        
        # Verify update didn't affect others
        self.assertEqual(self.db.read('user1')['name'], 'Alice')
        self.assertEqual(self.db.read('user2')['name'], 'Robert')
        self.assertEqual(self.db.read('user3')['name'], 'Charlie')
    
    def test_error_handling_integration(self):
        """Test error handling across operations."""
        # Test creating duplicate key
        self.db.create('duplicate', {'value': 1})
        with self.assertRaises(ValueError):
            self.db.create('duplicate', {'value': 2})
        
        # Test reading non-existent key
        with self.assertRaises(KeyError):
            self.db.read('nonexistent')
        
        # Test updating non-existent key
        with self.assertRaises(KeyError):
            self.db.update('nonexistent', {'value': 1})
        
        # Test deleting non-existent key
        with self.assertRaises(KeyError):
            self.db.delete('nonexistent')


class TestDatabaseCorruption(unittest.TestCase):
    """Integration tests for handling corrupted database files."""
    
    def setUp(self):
        """Set up test with corrupted database file."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        # Write invalid JSON to simulate corruption
        self.temp_file.write(b'{"invalid": json content}')
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_corrupted_file_recovery(self):
        """Test that corrupted files are handled gracefully."""
        # Should not raise exception, should start with empty data
        db = SimpleDatabase(self.temp_file.name)
        self.assertEqual(len(db.list_all()), 0)
        
        # Should be able to add new data
        db.create('recovery_test', {'status': 'recovered'})
        result = db.read('recovery_test')
        self.assertEqual(result['status'], 'recovered')


if __name__ == '__main__':
    unittest.main()