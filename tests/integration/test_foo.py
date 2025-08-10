"""Tests for the foo module.

This module contains tests for the basic utility functions in the project.
"""

from optimes.foo import foo


def test_foo() -> None:
    """Test the foo function returns the input string unchanged."""
    assert foo("foo") == "foo"
