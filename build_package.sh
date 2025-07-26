#!/bin/bash
# Script to build the pythonrules package from the correct directory

echo "Building PythonRules package..."
cd pythonrules || { echo "Error: pythonrules directory not found"; exit 1; }

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in pythonrules directory"
    exit 1
fi

# Install build if needed
python3 -m pip install --upgrade build

# Build the package
python3 -m build

echo "Build completed. Distribution files are in pythonrules/dist/"