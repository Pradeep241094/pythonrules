#!/bin/bash

# Script to publish to Test PyPI (for testing)

set -e

echo "🧪 Publishing to Test PyPI..."

# Check if package is built
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo "❌ No built packages found. Run ./build_pip_package.sh first"
    exit 1
fi

echo "📤 Uploading to Test PyPI..."
echo "⚠️  You will need to enter your TestPyPI API token when prompted"
echo "   Get your token from: https://test.pypi.org/manage/account/token/"

python3 -m twine upload --repository testpypi dist/*

echo ""
echo "✅ Package uploaded to Test PyPI!"
echo ""
echo "🧪 To test the installation from Test PyPI:"
echo "   pip install --index-url https://test.pypi.org/simple/ pyrulesrunner"
echo ""
echo "🌐 View your package at:"
echo "   https://test.pypi.org/project/pyrulesrunner/"