#!/usr/bin/env python3
"""
Setup script for the lightweight-test-runner package.
"""

from setuptools import setup, find_packages
import os

# Read the README file for the long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "A lightweight Python test runner with method-level discovery and coverage reporting."

# Read version from testrules.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'testrules', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return "1.0.0"

setup(
    name="pyrulesrunner",
    version=get_version(),
    author="Pradeep Margasahayam Prakash",
    author_email="pradeepprakash1024@gmail.com",
    description="A lightweight Python test runner with method-level discovery and coverage reporting",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Pradeep241094/pythonrules",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
    ],
    python_requires=">=3.7",
    install_requires=[
        # Core dependencies - none required, optional dependencies listed below
    ],
    extras_require={
        "coverage": ["coverage>=6.0"],
        "lint": ["flake8>=4.0"],
        "dev": ["coverage>=6.0", "flake8>=4.0"],
        "all": ["coverage>=6.0", "flake8>=4.0"],
    },
    entry_points={
        "console_scripts": [
            "testrules=testrules.cli:main",
            "pyrulesrunner=testrules.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "testrules": ["*.json", "examples/*.py"],
    },
    zip_safe=False,
    keywords="testing test-runner unittest coverage lint python",
    project_urls={
        "Bug Reports": "https://github.com/Pradeep241094/pythonrules/issues",
        "Source": "https://github.com/Pradeep241094/pythonrules",
        "Documentation": "https://github.com/Pradeep241094/pythonrules/README.md",
    },
)