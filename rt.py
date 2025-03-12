#! /usr/bin/python3
 
import re

# Identifies "snake case" and "kabab case"
# With the latter, it cannot start with a hyphen and an alpha character must follow a hyphen
# This is an attempt to prevent some subtraction operations from looking like identifiers
# Inclusion of whitespace can always help disambiguate the two.
pattern = re.compile(r"^[A-Za-z_]([A-Za-z0-9_]|-+[A-Za-z])*$")

# Test cases: (test string, expected match result)
test_cases = [
    ("a", True),
    ("Z", True),
    ("_", True),
    ("__", True),
    ("abc_123", True),
    ("abc-d123", True),
    ("valid_name", True),
    ("_valid_name", True),
    ("valid_name9", True),
    ("valid_9name", True),
    ("Valid-Name", True),
    ("Valid------Name", True),
    ("Valid-Name9", True),
    ("Valid_", True),
    ("a-b", True), # possible subtraction pattern

    ("-", False), # this is a minus
    ("abc-123", False), # possible subtraction
    ("1invalid", False),
    ("invalid-", False), # bad style or possible ending minus
]

for s, expected in test_cases:
    result = bool(pattern.fullmatch(s))
    status = "✅" if result == expected else "❌"
    print(f"{s!r}: {'Match' if result else 'No Match'} [{status}]")