#!/bin/bash

# Build script for lightweight-test-runner pip package

set -e

echo "🚀 Building pyrulesrunner pip package..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install --upgrade build twine

# Build the package
echo "🔨 Building package..."
python3 -m build

# Check the package
echo "🔍 Checking package..."
python3 -m twine check dist/*

echo "✅ Package built successfully!"
echo ""
echo "📁 Built files:"
ls -la dist/

echo ""
echo "🚀 To install locally for testing:"
echo "   pip install dist/pyrulesrunner-*.whl"
echo ""
echo "📤 To upload to PyPI (when ready):"
echo "   python -m twine upload dist/*"
echo ""
echo "🧪 To test the installation:"
echo "   pip install dist/pyrulesrunner-*.whl"
echo "   testrules --help"