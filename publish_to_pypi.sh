#!/bin/bash

# Script to publish to real PyPI (production)

set -e

echo "🚀 Publishing to PyPI..."

# Check if package is built
if [ ! -d "dist" ] || [ -z "$(ls -A dist)" ]; then
    echo "❌ No built packages found. Run ./build_pip_package.sh first"
    exit 1
fi

echo "⚠️  WARNING: This will publish to the REAL PyPI!"
echo "   Make sure you have tested on TestPyPI first"
echo "   This action cannot be undone!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Publication cancelled"
    exit 1
fi

echo "📤 Uploading to PyPI..."
echo "⚠️  You will need to enter your PyPI API token when prompted"
echo "   Get your token from: https://pypi.org/manage/account/token/"

python3 -m twine upload dist/*

echo ""
echo "✅ Package uploaded to PyPI!"
echo ""
echo "🎉 Your package is now available for installation:"
echo "   pip install pyrulesrunner"
echo ""
echo "🌐 View your package at:"
echo "   https://pypi.org/project/pyrulesrunner/"