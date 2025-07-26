#!/usr/bin/env python3
"""
Reporting functionality for the lightweight test runner.
"""

import os

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False

try:
    import flake8.api.legacy as flake8
    FLAKE8_AVAILABLE = True
except ImportError:
    FLAKE8_AVAILABLE = False


def report_test_summary(test_results):
    """
    Display test summary reporting with total tests, passed, failed counts,
    success rate percentage, and execution time information.
    
    Args:
        test_results: TestResult object containing test results
    """
    print("\n" + "=" * 60)
    print("🧪 TEST SUMMARY")
    print("=" * 60)
    
    # Display total tests, passed, and failed counts
    print(f"✅ Passed:        {test_results.passed}")
    print(f"❌ Failed:        {test_results.failed}")
    print(f"💥 Errors:        {test_results.errors}")
    print(f"📊 Total:         {test_results.total}")
    
    # Calculate and show success rate as percentage
    success_rate = test_results.get_success_rate()
    print(f"📈 Success Rate:  {success_rate:.2f}%")
    
    # Show execution time information
    print(f"⏱️  Execution Time: {test_results.duration:.2f} seconds")
    
    # Visual indicator based on results
    if test_results.failed == 0 and test_results.errors == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {test_results.failed + test_results.errors} test(s) failed or had errors")


def report_detailed_test_results(test_results):
    """
    Show individual test method results with full qualified names,
    display error details and tracebacks for failed tests,
    and format output with emoji and clear visual separation.
    
    Args:
        test_results: TestResult object containing test results
    """
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 60)
    
    # Show individual test method results with full qualified names
    for result in test_results.method_results:
        status_emoji = "✅" if result.status == "pass" else ("❌" if result.status == "fail" else "💥")
        status_text = result.status.upper()
        
        print(f"{status_emoji} {result.method.full_name} ... {status_text} ({result.duration:.3f}s)")
    
    # Display error details and tracebacks for failed tests
    failed_results = test_results.get_failed_results()
    if failed_results:
        print("\n" + "=" * 60)
        print("❌ FAILURE DETAILS")
        print("=" * 60)
        
        for i, result in enumerate(failed_results, 1):
            print(f"\n{i}. {result.method.full_name}")
            print("-" * 60)
            
            if result.status == "fail":
                print("FAILURE:")
            elif result.status == "error":
                print("ERROR:")
            
            # Display error details with proper formatting
            if result.error:
                print(result.error)
            
            # Display traceback if available
            if result.traceback_str:
                print("\nTraceback:")
                print(result.traceback_str)
            
            if i < len(failed_results):
                print("\n" + "-" * 60)


def generate_coverage_report(cov):
    """
    Generate console coverage report with line and branch coverage.
    
    Args:
        cov: Coverage object containing coverage data
        
    Returns:
        Dictionary containing coverage summary data
    """
    if not cov:
        print("⚠️ No coverage data available")
        return None
    
    try:
        # Get coverage data
        coverage_data = cov.get_data()
        
        if not coverage_data.measured_files():
            print("⚠️ No files were measured for coverage")
            return None
        
        # Generate coverage report
        print("\n📊 COVERAGE REPORT")
        print("=" * 60)
        
        # Print header
        print(f"{'Name':<30} {'Stmts':<8} {'Miss':<8} {'Branch':<8} {'BrPart':<8} {'Cover':<8}")
        print("-" * 60)
        
        total_statements = 0
        total_missing = 0
        total_branches = 0
        total_partial_branches = 0
        
        # Get coverage analysis for each file
        for filename in sorted(coverage_data.measured_files()):
            try:
                # Get analysis for this file - analysis2 returns a tuple
                analysis_result = cov.analysis2(filename)
                
                # analysis2 returns (filename, statements, excluded, missing, missing_formatted)
                if len(analysis_result) >= 4:
                    _, statements_list, _, missing_list = analysis_result[:4]
                    statements = len(statements_list)
                    missing = len(missing_list)
                else:
                    # Fallback to basic analysis
                    statements = 0
                    missing = 0
                    missing_list = []
                
                # Get branch coverage if available
                try:
                    branch_stats = cov.branch_stats().get(filename, (0, 0, 0))
                    branches = branch_stats[0] if len(branch_stats) > 0 else 0
                    partial_branches = branch_stats[1] if len(branch_stats) > 1 else 0
                except:
                    branches = 0
                    partial_branches = 0
                
                # Calculate coverage percentage
                if statements > 0:
                    coverage_percent = ((statements - missing) / statements) * 100
                else:
                    coverage_percent = 100.0
                
                # Accumulate totals
                total_statements += statements
                total_missing += missing
                total_branches += branches
                total_partial_branches += partial_branches
                
                # Format filename for display
                display_name = filename
                if len(display_name) > 28:
                    display_name = "..." + display_name[-25:]
                
                # Print file coverage
                print(f"{display_name:<30} {statements:<8} {missing:<8} {branches:<8} {partial_branches:<8} {coverage_percent:>6.1f}%")
                
                # Show missing lines if there are any
                if missing > 0 and len(missing_list) <= 10:  # Only show if not too many
                    missing_lines = sorted(missing_list)
                    missing_ranges = []
                    
                    if missing_lines:
                        # Group consecutive lines into ranges
                        start = missing_lines[0]
                        end = start
                        
                        for line in missing_lines[1:]:
                            if line == end + 1:
                                end = line
                            else:
                                if start == end:
                                    missing_ranges.append(str(start))
                                else:
                                    missing_ranges.append(f"{start}-{end}")
                                start = end = line
                        
                        # Add the last range
                        if start == end:
                            missing_ranges.append(str(start))
                        else:
                            missing_ranges.append(f"{start}-{end}")
                        
                        print(f"{'':<30} Missing: {', '.join(missing_ranges)}")
                
            except Exception as e:
                print(f"⚠️ Error analyzing coverage for {filename}: {e}")
                continue
        
        # Print totals
        print("-" * 60)
        
        # Calculate total coverage
        if total_statements > 0:
            total_coverage = ((total_statements - total_missing) / total_statements) * 100
        else:
            total_coverage = 100.0
        
        print(f"{'TOTAL':<30} {total_statements:<8} {total_missing:<8} {total_branches:<8} {total_partial_branches:<8} {total_coverage:>6.1f}%")
        
        # Coverage summary
        print(f"\n📈 COVERAGE SUMMARY:")
        print(f"   Lines covered: {total_statements - total_missing}/{total_statements} ({total_coverage:.1f}%)")
        if total_branches > 0:
            branch_coverage = ((total_branches - total_partial_branches) / total_branches) * 100 if total_branches > 0 else 100.0
            print(f"   Branches covered: {total_branches - total_partial_branches}/{total_branches} ({branch_coverage:.1f}%)")
        
        # Return summary data
        return {
            'total_statements': total_statements,
            'total_missing': total_missing,
            'total_branches': total_branches,
            'total_partial_branches': total_partial_branches,
            'line_coverage': total_coverage,
            'branch_coverage': ((total_branches - total_partial_branches) / total_branches) * 100 if total_branches > 0 else 100.0
        }
        
    except Exception as e:
        print(f"⚠️ Error generating coverage report: {e}")
        return None


def generate_html_coverage_report(cov, config):
    """
    Generate HTML coverage report using coverage package.
    
    Args:
        cov: Coverage object containing coverage data
        config: Config object containing HTML coverage settings
        
    Returns:
        True if successful, False otherwise
    """
    if not cov:
        print("⚠️ No coverage data available for HTML report")
        return False
    
    if not config.html_coverage:
        print("ℹ️ HTML coverage report generation is disabled in configuration")
        return False
    
    try:
        # Ensure the HTML coverage directory exists
        html_dir = config.html_coverage_dir
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
            print(f"📁 Created HTML coverage directory: {html_dir}")
        
        # Generate HTML report
        print(f"📄 Generating HTML coverage report...")
        cov.html_report(directory=html_dir)
        
        # Get the path to the main HTML file
        index_path = os.path.join(html_dir, 'index.html')
        
        if os.path.exists(index_path):
            # Convert to absolute path for better display
            abs_index_path = os.path.abspath(index_path)
            print(f"📁 HTML coverage report saved to: {abs_index_path}")
            print(f"🌐 Open in browser: file://{abs_index_path}")
            return True
        else:
            print(f"⚠️ HTML report was generated but index.html not found at expected location")
            return False
        
    except Exception as e:
        print(f"⚠️ Error generating HTML coverage report: {e}")
        return False


def run_lint(search_path=".", specific_files=None):
    """
    Run PEP8 style checks using flake8.
    
    Args:
        search_path: Directory to search for Python files (default: current directory)
        specific_files: List of specific files to check (optional)
        
    Returns:
        Number of style violations found
    """
    if not FLAKE8_AVAILABLE:
        print("⚠️ flake8 package not available. Install with: pip install flake8")
        return -1
    
    try:
        print("🔍 Running code style checks with flake8...")
        
        # Initialize flake8 style guide
        style_guide = flake8.get_style_guide()
        
        # Determine which files to check
        if specific_files:
            python_files = [f for f in specific_files if f.endswith('.py') and os.path.exists(f)]
        else:
            # Find all Python files to check
            python_files = []
            for root, dirs, files in os.walk(search_path):
                # Skip common directories that shouldn't be linted
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'htmlcov', '.coverage', 'venv', 'env', '.venv', '.env']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        python_files.append(file_path)
        
        if not python_files:
            print("⚠️ No Python files found to lint")
            return 0
        
        print(f"📁 Found {len(python_files)} Python files to check")
        
        # Run flake8 checks
        report = style_guide.check_files(python_files)
        
        # Get the number of violations from the report statistics
        error_stats = report.get_statistics('E')
        warning_stats = report.get_statistics('W')
        flake_stats = report.get_statistics('F')
        
        # Count total violations
        violation_count = len(error_stats) + len(warning_stats) + len(flake_stats)
        
        return violation_count
        
    except Exception as e:
        print(f"⚠️ Error running flake8 checks: {e}")
        return -1


def report_lint_results(violation_count):
    """
    Display lint results with appropriate formatting.
    
    Args:
        violation_count: Number of style violations found (-1 if error occurred)
    """
    print("\n" + "=" * 60)
    print("🔍 LINT RESULTS")
    print("=" * 60)
    
    if violation_count == -1:
        print("❌ Linting failed due to an error")
        print("📋 Please check the error message above for details")
    elif violation_count == 0:
        print("✅ No style violations found! Code follows PEP8 standards.")
        print("🎉 Your code is clean and well-formatted!")
    else:
        print(f"⚠️ Found {violation_count} style violation{'s' if violation_count != 1 else ''}")
        print("📋 Check the output above for details on violations")
        print("💡 Run a code formatter like 'black' or 'autopep8' to fix many issues automatically")