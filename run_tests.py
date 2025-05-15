#!/usr/bin/env python
"""
Test runner for the Blackhole Core project.
Run this script to execute all tests.
"""

import os
import sys
import unittest
import argparse

# Import our custom logger
try:
    from utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(message)s'))
    logger.addHandler(handler)

def discover_and_run_tests(test_dir=None, pattern=None, verbosity=1):
    """
    Discover and run tests in the specified directory.
    
    Args:
        test_dir (str): Directory containing tests (default: 'tests')
        pattern (str): Pattern to match test files (default: 'test_*.py')
        verbosity (int): Verbosity level (1-3)
        
    Returns:
        unittest.TestResult: The test result object
    """
    if test_dir is None:
        test_dir = 'tests'
    
    if pattern is None:
        pattern = 'test_*.py'
    
    logger.info(f"Discovering tests in {test_dir} matching pattern {pattern}")
    
    # Make sure the test directory exists
    if not os.path.exists(test_dir):
        logger.error(f"Test directory {test_dir} does not exist")
        return None
    
    # Discover tests
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern=pattern)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    logger.info(f"Running {suite.countTestCases()} tests...")
    result = runner.run(suite)
    
    return result

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description='Run tests for the Blackhole Core project')
    parser.add_argument('--dir', '-d', help='Directory containing tests (default: tests)', default='tests')
    parser.add_argument('--pattern', '-p', help='Pattern to match test files (default: test_*.py)', default='test_*.py')
    parser.add_argument('--verbosity', '-v', help='Verbosity level (1-3)', type=int, choices=[1, 2, 3], default=2)
    
    args = parser.parse_args()
    
    logger.info("Starting test runner...")
    result = discover_and_run_tests(args.dir, args.pattern, args.verbosity)
    
    if result:
        logger.info(f"Tests completed: {result.testsRun} run, {len(result.errors)} errors, {len(result.failures)} failures")
        
        if result.errors:
            logger.error("Errors:")
            for test, error in result.errors:
                logger.error(f"{test}: {error}")
        
        if result.failures:
            logger.error("Failures:")
            for test, failure in result.failures:
                logger.error(f"{test}: {failure}")
        
        if not result.errors and not result.failures:
            logger.info("All tests passed!")
            return 0
        else:
            return 1
    else:
        logger.error("No tests were run")
        return 1

if __name__ == '__main__':
    sys.exit(main())
