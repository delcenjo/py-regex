from pyregex.infrastructure.registry.schema.models import RegistryPattern


class DeleteValidator:
    """Validates if a deletion action is structurally permissible."""

    def validate(self, pattern: RegistryPattern) -> bool:
        """
        Performs structural and permission checks.
        (Future: Multi-user permission checks 'user.role == admin' would live here).
        """
        if not pattern or not pattern.name:
            raise ValueError("Pattern name is missing or invalid.")

        # Prevent deletion of protected/system patterns
        if pattern.metadata and pattern.metadata.origin == "system":
            raise PermissionError(
                f"Cannot delete system-provided pattern '{pattern.name}'."
            )

        return True
