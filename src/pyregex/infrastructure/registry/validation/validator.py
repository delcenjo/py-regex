import re
from typing import Tuple, List


class RegistryValidator:
    """Strict validation gates for entering the Registry."""

    def validate(self, name: str, pattern: str) -> Tuple[bool, List[str]]:
        errors = []

        if not name or not name.strip():
            errors.append("Name cannot be empty.")
        elif not re.match(r"^[a-zA-Z0-9_\-]+$", name):
            errors.append(
                "Name can only contain letters, numbers, underscores, and hyphens."
            )
        elif len(name) > 50:
            errors.append("Name is too long (max 50 characters).")

        if not pattern or not pattern.strip():
            errors.append("Pattern cannot be empty.")
        else:
            try:
                re.compile(pattern)
            except re.error as e:
                errors.append(f"Invalid regex compilation: {str(e)}")

        return len(errors) == 0, errors
