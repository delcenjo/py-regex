from typing import List
from pyregex.infrastructure.registry.commands.delete.resolver.pattern_resolver import (
    PatternResolver,
)
from pyregex.infrastructure.registry.commands.delete.validation.delete_validator import (
    DeleteValidator,
)
from pyregex.infrastructure.registry.commands.delete.dependency.dependency_checker import (
    DependencyChecker,
)
from pyregex.infrastructure.registry.commands.delete.safety.trash_manager import (
    TrashManager,
)
from pyregex.infrastructure.registry.commands.delete.execution.deleter import Deleter
from pyregex.infrastructure.registry.commands.delete.audit.audit_logger import (
    AuditLogger,
)
from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.registry.search.engine import SearchEngine
from pyregex.infrastructure.registry.storage.backend import StorageBackend
from pyregex.infrastructure.registry.indexing.indexer import MemoryIndexer
from pyregex.utils import ansi


class DeleteResolutionError(Exception):
    def __init__(self, target: str, suggestions: List[RegistryPattern]):
        self.suggestions = suggestions
        msg = f"Pattern '{target}' not found."
        super().__init__(msg)


class DeleteController:
    """Orchestrates the safe deletion pipeline."""

    def __init__(
        self,
        backend: StorageBackend,
        indexer: MemoryIndexer,
        search_engine: SearchEngine,
    ):
        self.resolver = PatternResolver(search_engine)
        self.validator = DeleteValidator()
        self.dependency_checker = DependencyChecker()
        self.trash_manager = TrashManager()
        self.deleter = Deleter(backend, indexer)
        self.audit = AuditLogger()

    def request_delete(self, target_name: str, force: bool = False) -> str:
        """
        Executes the deletion pipeline.
        Returns a rich status message or raises specific exceptions
        that the CLI needs to catch for interactive prompts.
        """
        # 1. Resolver Phase
        exact, suggestions = self.resolver.resolve(target_name)
        if not exact:
            raise DeleteResolutionError(target_name, suggestions)

        # 2. Validation Phase
        self.validator.validate(exact)

        # 3. Dependency Phase
        if not force:
            self.dependency_checker.check(exact)

        # 4. Safety/Execution Phase
        self.trash_manager.move_to_trash(exact)
        self.deleter.execute(exact)

        # 5. Audit Phase
        self.audit.log_deletion(exact.name, used_force=force, is_soft=True)

        return ansi.success(f"Pattern '{exact.name}' moved to trash successfully.")
