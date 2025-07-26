# Example Project Using Lightweight Test Runner

This is an example project demonstrating how to use the lightweight-test-runner package in a separate project.

## Setup

1. **Install the lightweight-test-runner package**:
   ```bash
   pip install lightweight-test-runner[all]
   ```

2. **Create your project structure**:
   ```
   example-project/
   ├── testrules.json          # Test configuration
   ├── src/                    # Your source code
   │   ├── calculator.py
   │   └── utils.py
   ├── tests/                  # Your test files
   │   ├── test_calculator.py
   │   ├── test_utils.py
   │   └── integration_test_api.py
   └── README.md
   ```

3. **Run your tests**:
   ```bash
   # Run all tests
   testrules
   
   # Run specific test types
   testrules unit
   testrules integration
   
   # Run with coverage and linting
   testrules check
   ```

## Configuration

The `testrules.json` file configures how tests are discovered and run.

## Example Usage

```bash
# From your project directory
cd example-project

# Run all tests
testrules --all

# Run only unit tests
testrules unit

# Run specific test modules
testrules test_calculator test_utils

# Run with custom config
testrules --config custom_config.json

# Run without coverage
testrules --no-coverage

# Run linting only
testrules lint

# Run comprehensive check (linting + all tests)
testrules check
```