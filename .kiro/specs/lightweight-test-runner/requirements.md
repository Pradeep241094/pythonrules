# Requirements Document

## Introduction

The Lightweight Test Runner is a simple, efficient Python testing framework that provides test discovery at the method level, code coverage reporting, and basic linting capabilities. Unlike the more complex PythonRules framework, this lightweight solution focuses on simplicity and ease of use while still providing detailed test results. The package will be installable via pip and configurable through a simple JSON file.

## Requirements

### 1. Test Discovery and Execution

**User Story:** As a Python developer, I want a simple way to discover and run tests at the method level for different test types, so that I can see which specific test methods pass or fail.

#### Acceptance Criteria

1. WHEN discovering tests THEN the system SHALL identify individual test methods within unittest.TestCase classes.
2. WHEN discovering tests THEN the system SHALL support test grouping through a simple configuration file.
3. WHEN executing tests THEN the system SHALL run each test method individually and report its status.
4. WHEN a test fails THEN the system SHALL provide clear error messages with traceback information.
5. IF no configuration file is present THEN the system SHALL discover all test files matching a standard pattern (e.g., test_*.py).
6. WHEN discovering tests THEN the system SHALL identify and categorize different test types:
   - Unit tests (typically in test_*.py files or *_test.py files)
   - Integration tests (typically in integration_test_*.py files or *_integration_test.py files)
   - End-to-end tests (typically in e2e_test_*.py files or *_e2e_test.py files)
   - Regression tests (typically in regression_test_*.py files or *_regression_test.py files)
7. WHEN running tests THEN the system SHALL support running specific test types (unit, integration, e2e, regression) through command-line arguments.

### 2. Reporting

**User Story:** As a Python developer, I want clear, concise test reports that show results for individual test methods, so that I can quickly identify and fix failing tests.

#### Acceptance Criteria

1. WHEN tests complete THEN the system SHALL display a summary of test results in the console.
2. WHEN displaying results THEN the system SHALL show the total number of tests, passed tests, and failed tests.
3. WHEN displaying results THEN the system SHALL calculate and show the success rate as a percentage.
4. WHEN a test fails THEN the system SHALL display the test name and error details.
5. WHEN tests complete THEN the system SHALL provide execution time information.

### 3. Code Coverage

**User Story:** As a Python developer, I want to see code coverage metrics for my tests, so that I can identify untested code and improve test coverage.

#### Acceptance Criteria

1. WHEN running tests THEN the system SHALL collect code coverage information.
2. WHEN tests complete THEN the system SHALL display a coverage summary in the console.
3. WHEN tests complete THEN the system SHALL generate an HTML coverage report for detailed analysis.
4. WHEN reporting coverage THEN the system SHALL show line and branch coverage percentages.
5. WHEN reporting coverage THEN the system SHALL identify uncovered lines of code.

### 4. Linting

**User Story:** As a Python developer, I want basic code quality checks integrated with my test runner, so that I can ensure my code follows style guidelines.

#### Acceptance Criteria

1. WHEN running the lint command THEN the system SHALL check code against PEP8 standards.
2. WHEN linting completes THEN the system SHALL display the number of style violations found.
3. WHEN style violations are found THEN the system SHALL provide information about their location and nature.
4. WHEN running the check command THEN the system SHALL run both linting and all tests.
5. IF no style violations are found THEN the system SHALL display a success message.

### 5. Configuration

**User Story:** As a Python developer, I want a simple way to configure test groups and settings, so that I can organize and run tests efficiently.

#### Acceptance Criteria

1. WHEN a configuration file is present THEN the system SHALL load test groupings from it.
2. WHEN defining test groups THEN the system SHALL support specifying lists of test modules for each group.
3. WHEN running a test group THEN the system SHALL execute all tests in that group.
4. WHEN no configuration file is present THEN the system SHALL use sensible defaults.
5. WHEN running the tool THEN the system SHALL support command-line arguments to specify test groups or individual modules.
6. WHEN configuring test types THEN the system SHALL allow customization of file patterns for each test type (unit, integration, e2e, regression).
7. WHEN loading configuration THEN the system SHALL support defining custom test types beyond the built-in ones.