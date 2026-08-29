"""Checks that decide what is allowed to be written or returned.

Holds the draft guard, the generate-and-retry loop, and the checks the
agent loop applies to a proposed action. No module in this package may
import a package that changes files.
"""
