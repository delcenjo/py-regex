"""Nebula Assistant Engine — Shared Types & Protocols."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional, Protocol, runtime_checkable
from datetime import datetime


# ── Enums ────────────────────────────────────────────────────────────


class ModuleCategory(Enum):
    """Top-level module categories in the assistant."""

    PERSONAL = "personal"
    WEB = "web"
    FINANCE = "finance"
    SECURITY = "security"
    DEVOPS = "devops"
    DATA = "data"
    NETWORKING = "networking"
    STANDARDS = "standards"
    I18N = "i18n"
    TEXT = "text"
    SCIENCE = "science"
    PROGRAMMING = "programming"
    AUTOMOTIVE = "automotive"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    STRUCTURED = "structured"
    SYSTEMS = "systems"
    TOOLS = "tools"
    UTILS = "utils"
    COMPLIANCE = "compliance"


class StepType(Enum):
    """Types of wizard steps."""

    MENU = auto()  # Select from a list
    TEXT = auto()  # Free-text input
    CONFIRM = auto()  # Yes/No
    MULTISELECT = auto()  # Pick multiple items
    NUMBER = auto()  # Numeric input
    REGEX = auto()  # Raw regex input
    INFO = auto()  # Display-only (no input)


class SessionState(Enum):
    """States in the assistant FSM."""

    IDLE = auto()
    BROWSING = auto()
    BROWSING_CATALOG = auto()
    IN_MODULE = auto()
    IN_WIZARD = auto()
    PREVIEWING = auto()
    FINALIZING = auto()
    HELP = auto()
    ERROR = auto()


class EventType(Enum):
    """Event types for the event bus."""

    SESSION_START = auto()
    SESSION_END = auto()
    MODULE_ENTER = auto()
    MODULE_EXIT = auto()
    WIZARD_START = auto()
    WIZARD_STEP = auto()
    WIZARD_COMPLETE = auto()
    WIZARD_CANCEL = auto()
    PATTERN_GENERATED = auto()
    PATTERN_SAVED = auto()
    PATTERN_TESTED = auto()
    ERROR_OCCURRED = auto()
    HELP_REQUESTED = auto()
    COMMAND_EXECUTED = auto()


# ── Data Classes ─────────────────────────────────────────────────────


@dataclass
class Choice:
    """A single choice in a menu step."""

    key: str
    label: str
    description: str = ""
    icon: str = ""
    disabled: bool = False
    condition: Optional[Callable[[], bool]] = None


@dataclass
class StepDefinition:
    """Declarative definition of a single wizard step."""

    id: str
    title: str
    step_type: StepType
    choices: list[Choice] = field(default_factory=list)
    prompt_text: str = "> "
    default: Optional[str] = None
    validator: Optional[Callable[[str], tuple[bool, str]]] = None
    condition: Optional[Callable[[dict], bool]] = None
    help_text: str = ""
    required: bool = True


@dataclass
class StepResult:
    """Result of executing a single wizard step."""

    step_id: str
    value: Any
    raw_input: str = ""
    cancelled: bool = False
    went_back: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class WizardResult:
    """Complete result of a wizard execution."""

    pattern: str
    builder_name: str
    tags: list[str] = field(default_factory=list)
    description: str = ""
    step_results: dict[str, StepResult] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)
    non_examples: list[str] = field(default_factory=list)
    success: bool = True
    cancelled: bool = False
    error: Optional[str] = None


@dataclass
class ModuleInfo:
    """Metadata about a registered module."""

    name: str
    category: ModuleCategory
    display_name: str
    description: str
    icon: str = ""
    wizard_count: int = 0
    commands: list[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class Event:
    """An event emitted during assistant operations."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineRequest:
    """A request flowing through the processing pipeline."""

    command: str
    args: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    raw_input: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PipelineResponse:
    """A response from the processing pipeline."""

    success: bool = True
    result: Any = None
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0


# ── Protocols ────────────────────────────────────────────────────────


@runtime_checkable
class Middleware(Protocol):
    """Protocol for pipeline middleware."""

    def process(
        self, request: PipelineRequest, next_handler: Callable
    ) -> PipelineResponse: ...


@runtime_checkable
class ModuleProtocol(Protocol):
    """Protocol that all assistant modules must satisfy."""

    @property
    def info(self) -> ModuleInfo: ...
    def get_wizards(self) -> dict[str, type]: ...
    def get_commands(self) -> dict[str, Callable]: ...


@runtime_checkable
class WizardProtocol(Protocol):
    """Protocol that all wizards must satisfy."""

    @property
    def name(self) -> str: ...
    @property
    def steps(self) -> list[StepDefinition]: ...
    def execute(self, session: Any) -> WizardResult: ...
