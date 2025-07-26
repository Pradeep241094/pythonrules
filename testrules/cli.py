#!/usr/bin/env python3
"""
Command-line interface for the lightweight test runner.
"""

import sys
import os
import json
import argparse

from .core import Config, TestRunner
from .reporting import (
    report_test_summary,
    report_detailed_test_results,
    generate_coverage_report,
    generate_html_coverage_report,
    run_lint,
    report_lint_results
)


def load_config(config_file="testrules.json"):
    """
    Load configuration from a JSON file if present, else use defaults.
    
    Args:
        config_file: Path to the configuration file
        
    Returns:
        Config object containing configuration settings
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                data = json.load(f)
            print(f"📄 Loaded configuration from {config_file}")
            return Config(data)
        else:
            print(f"📄 No configuration file found at {config_file}, using defaults")
            return Config()
    except json.JSONDecodeError as e:
        print(f"⚠️ Error parsing configuration file {config_file}: {e}")
        print("📄 Using default configuration")
        return Config()
    except Exception as e:
        print(f"⚠️ Error loading configuration file {config_file}: {e}")
        print("📄 Using default configuration")
        return Config()


def parse_arguments(args, config):
    """
    Parse command-line arguments and determine what action to take.
    
    Args:
        args: List of command-line arguments
        config: Config object containing test types and groups
        
    Returns:
        Dictionary containing parsed arguments
    """
    if not args:
        return {
            'action': 'test',
            'test_type': None,
            'modules': None,
            'group': None,
            'command_description': 'all tests'
        }
    
    # Handle help commands
    if len(args) == 1 and args[0] in ['help', '--help', '-h']:
        return {
            'action': 'help',
            'test_type': None,
            'modules': None,
            'group': None,
            'command_description': 'help'
        }
    
    # Handle single argument commands
    if len(args) == 1:
        command = args[0]
        
        # Special commands
        if command == "lint":
            return {
                'action': 'lint',
                'test_type': None,
                'modules': None,
                'group': None,
                'command_description': 'linting only'
            }
        elif command == "check":
            return {
                'action': 'check',
                'test_type': None,
                'modules': None,
                'group': None,
                'command_description': 'comprehensive check (linting + all tests)'
            }
        elif command in ["--all", "all"]:
            return {
                'action': 'test',
                'test_type': None,
                'modules': None,
                'group': None,
                'command_description': 'all tests'
            }
        # Test type commands
        elif command in config.get_test_types():
            return {
                'action': 'test',
                'test_type': command,
                'modules': None,
                'group': None,
                'command_description': f'{command} tests'
            }
        # Test group commands
        elif command in config.test_groups:
            return {
                'action': 'test',
                'test_type': None,
                'modules': None,
                'group': command,
                'command_description': f'test group "{command}"'
            }
        # Single module
        else:
            return {
                'action': 'test',
                'test_type': None,
                'modules': [command],
                'group': None,
                'command_description': f'module "{command}"'
            }
    
    # Multiple arguments - treat as modules
    return {
        'action': 'test',
        'test_type': None,
        'modules': args,
        'group': None,
        'command_description': f'modules: {", ".join(args)}'
    }


def create_argument_parser():
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser object
    """
    parser = argparse.ArgumentParser(
        prog='testrules',
        description='Lightweight Test Runner - A simple, efficient Python testing framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  testrules                          # Run all tests
  testrules --all                    # Run all tests (explicit)
  testrules unit                     # Run unit tests only
  testrules integration              # Run integration tests only
  testrules e2e                      # Run end-to-end tests only
  testrules regression               # Run regression tests only
  testrules lint                     # Run linting only
  testrules check                    # Run both linting and all tests
  testrules core                     # Run tests in 'core' group (if defined)
  testrules test_module1 test_module2  # Run specific test modules
  testrules --config custom.json    # Use custom configuration file
        """
    )
    
    parser.add_argument(
        'targets',
        nargs='*',
        help='Test targets: test types (unit, integration, e2e, regression), test groups, or module names'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests (default if no targets specified)'
    )
    
    parser.add_argument(
        '--config',
        default='testrules.json',
        help='Configuration file path (default: testrules.json)'
    )
    
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage collection'
    )
    
    parser.add_argument(
        '--lint-only',
        action='store_true',
        help='Run linting only'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Run comprehensive check (linting + all tests)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def show_help():
    """
    Display help information for the test runner.
    """
    help_text = """
🚀 Lightweight Test Runner

USAGE:
    testrules [COMMAND|MODULE...]

COMMANDS:
    (no args)           Run all tests
    --all               Run all tests (explicit)
    unit               Run unit tests only
    integration        Run integration tests only  
    e2e                Run end-to-end tests only
    regression         Run regression tests only
    lint               Run code style checks only
    check              Run both linting and all tests
    help, --help, -h   Show this help message

TEST GROUPS:
    You can run predefined test groups from your configuration file:
    testrules [GROUP_NAME]

MODULES:
    Run specific test modules:
    testrules module1 module2 ...

EXAMPLES:
    testrules                          # Run all tests
    testrules --all                    # Run all tests (explicit)
    testrules unit                     # Run unit tests only
    testrules integration              # Run integration tests only
    testrules e2e                      # Run end-to-end tests only
    testrules regression               # Run regression tests only
    testrules lint                     # Run linting only
    testrules check                    # Run both linting and all tests
    testrules core                     # Run tests in 'core' group (if defined in config)
    testrules test_module1 test_module2  # Run specific test modules
    testrules --config custom.json    # Use custom configuration file

CONFIGURATION:
    Configuration is loaded from testrules.json if present.
    See documentation for configuration options.
    """
    print(help_text)


def main(args=None):
    """
    Main entry point for the test runner CLI.
    
    Args:
        args: Command line arguments (uses sys.argv if None)
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if args is None:
        args = sys.argv[1:]
    
    print("🚀 Lightweight Test Runner")
    print("=" * 50)
    
    # Parse arguments using argparse for better handling
    parser = create_argument_parser()
    
    try:
        parsed_args = parser.parse_args(args)
    except SystemExit as e:
        return e.code
    
    # Load configuration
    config = load_config(parsed_args.config)
    
    # Determine action based on parsed arguments
    if parsed_args.lint_only:
        action = 'lint'
        command_description = 'linting only'
    elif parsed_args.check:
        action = 'check'
        command_description = 'comprehensive check (linting + all tests)'
    elif parsed_args.all or not parsed_args.targets:
        action = 'test'
        command_description = 'all tests'
        test_type = None
        modules = None
        group = None
    else:
        # Parse targets using the original logic
        parsed_targets = parse_arguments(parsed_args.targets, config)
        action = parsed_targets['action']
        command_description = parsed_targets['command_description']
        test_type = parsed_targets.get('test_type')
        modules = parsed_targets.get('modules')
        group = parsed_targets.get('group')
    
    # Handle help command
    if action == 'help':
        show_help()
        return 0
    
    # Handle lint command
    if action == 'lint':
        print("🔍 Running code style checks...")
        violation_count = run_lint()
        report_lint_results(violation_count)
        return 1 if violation_count > 0 else 0
    
    # Handle check command (lint + tests)
    lint_failed = False
    if action == 'check':
        print("🔍 Running comprehensive check (linting + all tests)")
        
        # First run linting
        violation_count = run_lint()
        report_lint_results(violation_count)
        
        # Store lint results for final exit code
        lint_failed = violation_count > 0
        
        print("\n" + "=" * 50)
        print("🧪 Now running all tests...")
        print("=" * 50)
        
        # Set up for running all tests
        test_type = None
        modules = None
        group = None
    
    # For test actions, set up variables if not already set
    if action == 'test' and 'test_type' not in locals():
        test_type = None
        modules = None
        group = None
    
    print(f"Command: {command_description}")
    
    # Show configuration information
    print(f"\n📋 Configuration loaded:")
    print(f"   Test types: {config.get_test_types()}")
    print(f"   Test groups: {list(config.test_groups.keys())}")
    print(f"   Coverage enabled: {config.coverage_enabled and not parsed_args.no_coverage}")
    print(f"   HTML coverage: {config.html_coverage}")
    
    # Create and run test runner
    runner = TestRunner(config)
    
    # Determine coverage setting
    collect_coverage = config.coverage_enabled and not parsed_args.no_coverage
    
    print(f"\n🔍 Discovering tests...")
    test_results, coverage_obj = runner.run_tests(
        test_type=test_type,
        modules=modules,
        group=group,
        collect_coverage=collect_coverage
    )
    
    if test_results.total == 0:
        print("❌ No tests were run!")
        return 1
    
    # Display test summary reporting
    report_test_summary(test_results)
    
    # Display detailed test reporting
    report_detailed_test_results(test_results)
    
    # Generate coverage report if coverage was collected
    if coverage_obj and collect_coverage:
        coverage_summary = generate_coverage_report(coverage_obj)
        
        # Generate HTML coverage report if enabled
        if config.html_coverage:
            generate_html_coverage_report(coverage_obj, config)
    
    # Show timing breakdown for slowest tests
    if test_results.method_results:
        print(f"\n" + "=" * 60)
        print("⏱️ TIMING BREAKDOWN")
        print("=" * 60)
        # Sort by duration (slowest first)
        sorted_results = sorted(test_results.method_results, key=lambda x: x.duration, reverse=True)
        
        # Show top 5 slowest tests
        top_slow = sorted_results[:5]
        for result in top_slow:
            print(f"   {result.method.full_name}: {result.duration:.3f}s")
    
    # Return appropriate exit code
    if test_results.failed > 0 or test_results.errors > 0 or lint_failed:
        if lint_failed and (test_results.failed > 0 or test_results.errors > 0):
            print(f"\n❌ Both linting and tests failed. Please check above for details.")
        elif lint_failed:
            print(f"\n❌ Linting failed but tests passed. Please fix style violations.")
        else:
            print(f"\n❌ Some tests failed. Please check above for details.")
        return 1
    else:
        print(f"\n✅ All checks passed successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())