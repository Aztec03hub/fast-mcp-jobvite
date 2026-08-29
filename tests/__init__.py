"""Test package.

Present so `from .conftest import ...` resolves under pytest's default
`prepend` import mode. Without it the relative import raises at
collection.
"""
