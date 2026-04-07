"""Nebula Wizard Framework — Input Validators."""

from __future__ import annotations
import re


def regex_validator(value: str) -> tuple[bool, str]:
    """Validate that input is a valid regex."""
    try:
        re.compile(value)
        return True, ""
    except re.error as e:
        return False, f"Invalid regex: {e}"


def range_validator(min_val: int, max_val: int) -> callable:
    """Create a validator for numeric ranges."""

    def validate(value: str) -> tuple[bool, str]:
        try:
            n = int(value)
            if min_val <= n <= max_val:
                return True, ""
            return False, f"Value must be between {min_val} and {max_val}"
        except ValueError:
            return False, "Please enter a valid number"

    return validate


def length_validator(min_len: int = 0, max_len: int = 1000) -> callable:
    """Create a validator for string length."""

    def validate(value: str) -> tuple[bool, str]:
        if len(value) < min_len:
            return False, f"Minimum {min_len} characters required"
        if len(value) > max_len:
            return False, f"Maximum {max_len} characters allowed"
        return True, ""

    return validate


def pattern_validator(pattern: str, error_msg: str = "Invalid format") -> callable:
    """Create a validator based on a regex pattern."""
    compiled = re.compile(pattern)

    def validate(value: str) -> tuple[bool, str]:
        if compiled.match(value):
            return True, ""
        return False, error_msg

    return validate


def enum_validator(valid_values: list[str], case_insensitive: bool = True) -> callable:
    """Create a validator for a fixed set of values."""

    def validate(value: str) -> tuple[bool, str]:
        check = value.lower() if case_insensitive else value
        valid = [v.lower() for v in valid_values] if case_insensitive else valid_values
        if check in valid:
            return True, ""
        return False, f"Must be one of: {', '.join(valid_values)}"

    return validate


def not_empty(value: str) -> tuple[bool, str]:
    """Validate that input is not empty."""
    if value.strip():
        return True, ""
    return False, "This field cannot be empty"


def email_validator(value: str) -> tuple[bool, str]:
    """Validate email format."""
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
        return True, ""
    return False, "Invalid email format"


def domain_validator(value: str) -> tuple[bool, str]:
    """Validate domain name format."""
    if re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$", value):
        return True, ""
    return False, "Invalid domain format"


def ip_validator(value: str) -> tuple[bool, str]:
    """Validate IPv4 address."""
    parts = value.split(".")
    if len(parts) != 4:
        return False, "Invalid IP address"
    try:
        if all(0 <= int(p) <= 255 for p in parts):
            return True, ""
    except ValueError:
        pass
    return False, "Invalid IP address"


def csv_list_validator(value: str) -> tuple[bool, str]:
    """Validate comma-separated values."""
    parts = [p.strip() for p in value.split(",") if p.strip()]
    if parts:
        return True, ""
    return False, "Enter at least one value"


def compose(*validators) -> callable:
    """Compose multiple validators into one (all must pass)."""

    def validate(value: str) -> tuple[bool, str]:
        for v in validators:
            ok, msg = v(value)
            if not ok:
                return False, msg
        return True, ""

    return validate
