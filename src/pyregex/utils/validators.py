"""Input validation utilities."""

from __future__ import annotations

import re


def validate_regex(pattern: str) -> tuple[bool, str]:
    """Validate that a string is a valid regex pattern.

    Returns:
        Tuple of (is_valid, error_message). error_message is empty if valid.
    """
    try:
        re.compile(pattern)
        return True, ""
    except re.error as e:
        return False, str(e)


def validate_name(name: str) -> tuple[bool, str]:
    """Validate a pattern name (alphanumeric, underscores, hyphens, 1-64 chars).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not name:
        return False, "Name cannot be empty."
    if len(name) > 64:
        return False, "Name must be 64 characters or fewer."
    if not re.match(r"^[a-zA-Z0-9_\-]+$", name):
        return False, "Name must contain only letters, digits, underscores or hyphens."
    return True, ""


def parse_flags(
    ignore_case: bool = False,
    multiline: bool = False,
    dotall: bool = False,
    verbose: bool = False,
) -> int:
    """Build re flags integer from boolean options."""
    flags = 0
    if ignore_case:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.MULTILINE
    if dotall:
        flags |= re.DOTALL
    if verbose:
        flags |= re.VERBOSE
    return flags


def flags_to_list(flags: int) -> list[str]:
    """Convert re flags integer to list of flag names."""
    result: list[str] = []
    if flags & re.IGNORECASE:
        result.append("IGNORECASE")
    if flags & re.MULTILINE:
        result.append("MULTILINE")
    if flags & re.DOTALL:
        result.append("DOTALL")
    if flags & re.VERBOSE:
        result.append("VERBOSE")
    return result


def flags_from_list(flag_names: list[str]) -> int:
    """Convert list of flag names to re flags integer."""
    mapping = {
        "IGNORECASE": re.IGNORECASE,
        "MULTILINE": re.MULTILINE,
        "DOTALL": re.DOTALL,
        "VERBOSE": re.VERBOSE,
    }
    flags = 0
    for name in flag_names:
        flags |= mapping.get(name.upper(), 0)
    return flags
