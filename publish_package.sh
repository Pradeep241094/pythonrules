#!/bin/bash
# Script to publish the pythonrules package from the correct directory

echo "Publishing PythonRules package..."
cd pythonrules || { echo "Error: pythonrules directory not found"; exit 1; }

# Check if pyproject.toml exists
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found in pythonrules directory"
    exit 1
fi

# Check if dist directory exists
if [ ! -d "dist" ]; then
    echo "Error: dist directory not found. Run ./build_package.sh first."
    exit 1
fi

# Install twine if needed
python3 -m pip install --upgrade twine

# Check the distribution files
echo "Checking distribution files..."
python3 -m twine check dist/*

# Ask if user wants to publish to TestPyPI or PyPI
read -p "Publish to TestPyPI? (y/n): " test_pypi
if [[ $test_pypi == "y" || $test_pypi == "Y" ]]; then
    echo "Publishing to TestPyPI..."
    python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
else
    read -p "Publish to PyPI? (y/n): " pypi
    if [[ $pypi == "y" || $pypi == "Y" ]]; then
        echo "Publishing to PyPI..."
        python3 -m twine upload dist/*
    else
        echo "Aborted. No files were uploaded."
    fi
fi