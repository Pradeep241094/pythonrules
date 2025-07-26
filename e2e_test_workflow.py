#!/usr/bin/env python3
"""
End-to-end tests for complete user workflows.
These tests simulate real user interactions from start to finish.
"""

import unittest
import tempfile
import os
import json
import subprocess
import sys


class UserWorkflowSystem:
    """System that simulates a complete user workflow."""
    
    def __init__(self, data_dir):
        """Initialize the workflow system."""
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, 'users.json')
        self.sessions_file = os.path.join(data_dir, 'sessions.json')
        self.ensure_data_files()
    
    def ensure_data_files(self):
        """Ensure data files exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump({}, f)
    
    def register_user(self, username, email, password):
        """Register a new user."""
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        if username in users:
            raise ValueError(f"User {username} already exists")
        
        users[username] = {
            'email': email,
            'password': password,  # In real system, this would be hashed
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
        
        return {'username': username, 'status': 'registered'}
    
    def login_user(self, username, password):
        """Login a user and create session."""
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        if username not in users:
            raise ValueError(f"User {username} not found")
        
        if users[username]['password'] != password:
            raise ValueError("Invalid password")
        
        # Create session
        session_id = f"session_{username}_123"
        
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        sessions[session_id] = {
            'username': username,
            'created_at': '2024-01-01T00:00:00Z',
            'active': True
        }
        
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return {'session_id': session_id, 'username': username}
    
    def get_user_profile(self, session_id):
        """Get user profile using session."""
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        if session_id not in sessions or not sessions[session_id]['active']:
            raise ValueError("Invalid or expired session")
        
        username = sessions[session_id]['username']
        
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        user_data = users[username].copy()
        del user_data['password']  # Don't return password
        user_data['username'] = username
        
        return user_data
    
    def logout_user(self, session_id):
        """Logout user and deactivate session."""
        with open(self.sessions_file, 'r') as f:
            sessions = json.load(f)
        
        if session_id not in sessions:
            raise ValueError("Session not found")
        
        sessions[session_id]['active'] = False
        
        with open(self.sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return {'status': 'logged_out'}


class TestCompleteUserWorkflow(unittest.TestCase):
    """End-to-end tests for complete user workflows."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.system = UserWorkflowSystem(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_user_registration_and_login_workflow(self):
        """Test complete workflow from registration to logout."""
        # Step 1: Register user
        registration_result = self.system.register_user(
            'testuser', 'test@example.com', 'password123'
        )
        self.assertEqual(registration_result['status'], 'registered')
        self.assertEqual(registration_result['username'], 'testuser')
        
        # Step 2: Login user
        login_result = self.system.login_user('testuser', 'password123')
        self.assertIn('session_id', login_result)
        self.assertEqual(login_result['username'], 'testuser')
        session_id = login_result['session_id']
        
        # Step 3: Get user profile
        profile = self.system.get_user_profile(session_id)
        self.assertEqual(profile['username'], 'testuser')
        self.assertEqual(profile['email'], 'test@example.com')
        self.assertNotIn('password', profile)  # Password should not be returned
        
        # Step 4: Logout user
        logout_result = self.system.logout_user(session_id)
        self.assertEqual(logout_result['status'], 'logged_out')
        
        # Step 5: Verify session is no longer valid
        with self.assertRaises(ValueError) as context:
            self.system.get_user_profile(session_id)
        self.assertIn('Invalid or expired session', str(context.exception))
    
    def test_multiple_users_workflow(self):
        """Test workflow with multiple users."""
        users = [
            ('alice', 'alice@example.com', 'alice123'),
            ('bob', 'bob@example.com', 'bob456'),
            ('charlie', 'charlie@example.com', 'charlie789')
        ]
        
        sessions = []
        
        # Register and login all users
        for username, email, password in users:
            # Register
            reg_result = self.system.register_user(username, email, password)
            self.assertEqual(reg_result['status'], 'registered')
            
            # Login
            login_result = self.system.login_user(username, password)
            sessions.append(login_result['session_id'])
            
            # Verify profile
            profile = self.system.get_user_profile(login_result['session_id'])
            self.assertEqual(profile['username'], username)
            self.assertEqual(profile['email'], email)
        
        # Logout all users
        for session_id in sessions:
            logout_result = self.system.logout_user(session_id)
            self.assertEqual(logout_result['status'], 'logged_out')
    
    def test_error_scenarios_in_workflow(self):
        """Test error handling in complete workflows."""
        # Test duplicate registration
        self.system.register_user('duplicate', 'dup@example.com', 'pass123')
        with self.assertRaises(ValueError) as context:
            self.system.register_user('duplicate', 'dup2@example.com', 'pass456')
        self.assertIn('already exists', str(context.exception))
        
        # Test login with non-existent user
        with self.assertRaises(ValueError) as context:
            self.system.login_user('nonexistent', 'password')
        self.assertIn('not found', str(context.exception))
        
        # Test login with wrong password
        self.system.register_user('wrongpass', 'wrong@example.com', 'correct')
        with self.assertRaises(ValueError) as context:
            self.system.login_user('wrongpass', 'incorrect')
        self.assertIn('Invalid password', str(context.exception))
        
        # Test profile access with invalid session
        with self.assertRaises(ValueError) as context:
            self.system.get_user_profile('invalid_session')
        self.assertIn('Invalid or expired session', str(context.exception))


class TestSystemIntegrationWithExternalTools(unittest.TestCase):
    """Test integration with external tools and processes."""
    
    def test_python_script_execution(self):
        """Test that Python scripts can be executed successfully."""
        # Create a simple Python script
        script_content = '''
import sys
import json

def main():
    data = {"message": "Hello from external script", "args": sys.argv[1:]}
    print(json.dumps(data))

if __name__ == "__main__":
    main()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Execute the script
            result = subprocess.run(
                [sys.executable, script_path, 'arg1', 'arg2'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.assertEqual(result.returncode, 0)
            
            # Parse the output
            output_data = json.loads(result.stdout.strip())
            self.assertEqual(output_data['message'], 'Hello from external script')
            self.assertEqual(output_data['args'], ['arg1', 'arg2'])
            
        finally:
            os.unlink(script_path)
    
    def test_file_system_operations_workflow(self):
        """Test complete file system operations workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory structure
            subdir = os.path.join(temp_dir, 'subdir')
            os.makedirs(subdir)
            
            # Create files
            file1 = os.path.join(temp_dir, 'file1.txt')
            file2 = os.path.join(subdir, 'file2.json')
            
            with open(file1, 'w') as f:
                f.write('Hello World')
            
            with open(file2, 'w') as f:
                json.dump({'key': 'value'}, f)
            
            # Verify files exist and have correct content
            self.assertTrue(os.path.exists(file1))
            self.assertTrue(os.path.exists(file2))
            
            with open(file1, 'r') as f:
                content1 = f.read()
            self.assertEqual(content1, 'Hello World')
            
            with open(file2, 'r') as f:
                content2 = json.load(f)
            self.assertEqual(content2, {'key': 'value'})
            
            # List directory contents
            contents = os.listdir(temp_dir)
            self.assertIn('file1.txt', contents)
            self.assertIn('subdir', contents)
            
            subdir_contents = os.listdir(subdir)
            self.assertIn('file2.json', subdir_contents)


if __name__ == '__main__':
    unittest.main()