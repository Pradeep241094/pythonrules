#!/usr/bin/env python3
"""
Script to run tests for the simple-project using pythonrules.
"""

import os
import sys
import subprocess

def main():
    """Run the tests for the simple-project."""
    # Change to the simple-project directory
    os.chdir('pythonrules/examples/simple-project')
    
    # First, let's run the tests using pytest directly to verify they work
    print("Running tests with pytest:")
    pytest_result = subprocess.run(['python3', '-m', 'pytest', 'tests/unit/test_calculator.py', '-v'], 
                                  capture_output=True, text=True)
    
    print(pytest_result.stdout)
    if pytest_result.stderr:
        print(pytest_result.stderr)
    
    print("\n" + "="*80 + "\n")
    
    # Now, let's run the tests using pythonrules
    print("Running tests with pythonrules:")
    pythonrules_result = subprocess.run(['pythonrules', 'run', 'unit', '--format', 'text', '--coverage'], 
                                       capture_output=True, text=True)
    
    print(pythonrules_result.stdout)
    if pythonrules_result.stderr:
        print(pythonrules_result.stderr)
    
    # Return the exit code from the pythonrules run
    return pythonrules_result.returncode

if __name__ == '__main__':
    sys.exit(main())