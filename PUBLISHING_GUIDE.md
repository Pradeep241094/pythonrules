# Publishing Guide for Lightweight Test Runner

This guide explains how to publish the lightweight-test-runner package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)
   - [PyPI](https://pypi.org/account/register/) (for production)

2. **API Tokens**: Generate API tokens for both:
   - [TestPyPI Token](https://test.pypi.org/manage/account/token/)
   - [PyPI Token](https://pypi.org/manage/account/token/)

3. **Dependencies**: Ensure you have the required tools:
   ```bash
   pip install build twine
   ```

## Step-by-Step Publishing Process

### 1. Build the Package

```bash
./build_pip_package.sh
```

This will:
- Clean previous builds
- Install build dependencies
- Build both source distribution (.tar.gz) and wheel (.whl)
- Validate the package

### 2. Test on TestPyPI (Recommended)

```bash
./publish_to_testpypi.sh
```

When prompted, enter your TestPyPI API token.

### 3. Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ lightweight-test-runner
testrules --help
```

### 4. Publish to Production PyPI

Only after testing on TestPyPI:

```bash
./publish_to_pypi.sh
```

When prompted:
1. Confirm you want to publish to production
2. Enter your PyPI API token

### 5. Verify Installation

```bash
pip install lightweight-test-runner
testrules --help
```

## Package Information

- **Package Name**: `lightweight-test-runner`
- **Version**: 1.0.0
- **Author**: Pradeep Margasahayam Prakash
- **License**: MIT
- **Python Support**: 3.7+

## Features

- Method-level test discovery
- Multiple test types (unit, integration, e2e, regression)
- Test groups and patterns
- Code coverage reporting
- Linting integration
- Command-line interface

## Usage Examples

After installation, users can:

```bash
# Install the package
pip install lightweight-test-runner

# Run all tests
testrules

# Run specific test types
testrules unit
testrules integration
testrules e2e
testrules regression

# Run with coverage
testrules --all

# Run linting
testrules lint

# Run comprehensive check
testrules check

# Use custom configuration
testrules --config my_config.json
```

## Configuration

Users can create a `testrules.json` file in their project root:

```json
{
  "test_patterns": {
    "unit": ["test_*.py", "*_test.py"],
    "integration": ["integration_*.py"],
    "e2e": ["e2e_*.py"]
  },
  "test_groups": {
    "fast": ["test_utils", "test_models"],
    "slow": ["test_integration", "test_e2e"]
  },
  "coverage_enabled": true,
  "html_coverage": true
}
```

## Troubleshooting

### Common Issues

1. **Package Name Already Exists**
   - Choose a different name
   - Update `setup.py` and `pyproject.toml`

2. **Authentication Errors**
   - Verify your API token is correct
   - Make sure you're using the right token for the right repository

3. **Build Errors**
   - Check all required files are present
   - Verify Python syntax in all modules
   - Ensure dependencies are correctly specified

### Getting Help

- Check the [PyPI Help](https://pypi.org/help/)
- Review [Python Packaging Guide](https://packaging.python.org/)
- Test thoroughly on TestPyPI before publishing to production

## Post-Publication

After successful publication:

1. **Update Documentation**: Ensure README.md reflects the published package
2. **Create GitHub Release**: Tag the version and create a release
3. **Monitor Usage**: Check download statistics and user feedback
4. **Plan Updates**: Consider version updates and new features

## Version Management

For future updates:

1. Update version in `pyproject.toml` and `testrules/__init__.py`
2. Update CHANGELOG.md with changes
3. Rebuild and republish
4. Create new GitHub release tag

Remember: Once published to PyPI, you cannot delete or modify a version. Always test thoroughly on TestPyPI first!