# tests/test_main.py

import pytest
from main import factorial, divide, is_even

def test_factorial():
    assert factorial(5) == 120  # This will fail due to the SyntaxError in factorial

def test_divide():
    assert divide(10, 2) == 5  # This will fail due to the SyntaxError in divide

def test_is_even():
    assert is_even(4) is True  # This will fail due to the logical error in is_even
    assert is_even(5) is False