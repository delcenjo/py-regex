"""Nebula Assistant Engine — Error Hierarchy."""

from __future__ import annotations


class AssistantError(Exception):
    """Base exception for all assistant errors."""

    def __init__(self, message: str = "", code: str = "ASSISTANT_ERROR"):
        self.code = code
        super().__init__(message)


class WizardError(AssistantError):
    """Errors during wizard execution."""

    def __init__(self, message: str = "", wizard_name: str = "", step_id: str = ""):
        self.wizard_name = wizard_name
        self.step_id = step_id
        super().__init__(message, code="WIZARD_ERROR")


class WizardCancelledError(WizardError):
    """Raised when a user cancels a wizard."""

    def __init__(self, wizard_name: str = "", step_id: str = ""):
        super().__init__("Wizard cancelled by user", wizard_name, step_id)
        self.code = "WIZARD_CANCELLED"


class ModuleError(AssistantError):
    """Errors during module operations."""

    def __init__(self, message: str = "", module_name: str = ""):
        self.module_name = module_name
        super().__init__(message, code="MODULE_ERROR")


class ModuleNotFoundError(ModuleError):
    """Raised when a requested module is not registered."""

    def __init__(self, module_name: str = ""):
        super().__init__(f"Module not found: {module_name}", module_name)
        self.code = "MODULE_NOT_FOUND"


class SessionError(AssistantError):
    """Errors in session state management."""

    def __init__(self, message: str = ""):
        super().__init__(message, code="SESSION_ERROR")


class RouterError(AssistantError):
    """Errors in command routing."""

    def __init__(self, message: str = "", command: str = ""):
        self.command = command
        super().__init__(message, code="ROUTER_ERROR")


class ValidationError(AssistantError):
    """Input validation failures."""

    def __init__(self, message: str = "", field: str = "", value: str = ""):
        self.field = field
        self.value = value
        super().__init__(message, code="VALIDATION_ERROR")


class PipelineError(AssistantError):
    """Errors in the request/response pipeline."""

    def __init__(self, message: str = "", stage: str = ""):
        self.stage = stage
        super().__init__(message, code="PIPELINE_ERROR")
