"""Nebula Assistant Engine — Main Orchestrator."""

from __future__ import annotations
from typing import Any, Optional

from pyregex.presentation.assistant.core.types import (
    SessionState,
    EventType,
    PipelineRequest,
    PipelineResponse,
    ModuleCategory,
)
from pyregex.presentation.assistant.core.session import SessionContext
from pyregex.presentation.assistant.core.registry import ModuleRegistry
from pyregex.presentation.assistant.core.router import Router, RouteType
from pyregex.presentation.assistant.core.events import EventBus
from pyregex.presentation.assistant.core.pipeline import Pipeline
from pyregex.presentation.assistant.core.config import AssistantConfig
from pyregex.presentation.assistant.core.state.machine import StateMachine
from pyregex.presentation.assistant.core.middleware.handlers import (
    ValidationMiddleware,
    LoggingMiddleware,
    TimingMiddleware,
    ErrorHandlerMiddleware,
)


class AssistantEngine:
    """
    Central orchestrator for the Nebula Assistant Engine.

    Wires together:
    - Session management (state, navigation, history)
    - Module registry (plugin discovery and lookup)
    - Command router (input → target resolution)
    - Event bus (lifecycle hooks)
    - Pipeline (middleware chain)
    - State machine (navigation flow control)

    This is the single entrypoint accessed by the shell/REPL.
    """

    def __init__(self, cli: Any, config: Optional[AssistantConfig] = None):
        self.cli = cli
        self.config = config or AssistantConfig()

        # Core systems
        self.events = EventBus()
        self.session = SessionContext()
        self.registry = ModuleRegistry(event_bus=self.events)
        self.router = Router(registry=self.registry, event_bus=self.events)
        self.fsm = StateMachine()

        # Pipeline
        self.pipeline = Pipeline(event_bus=self.events)
        self._timing = TimingMiddleware()
        self._logging = LoggingMiddleware()
        self.pipeline.use(ErrorHandlerMiddleware())
        self.pipeline.use(self._timing)
        self.pipeline.use(self._logging)
        self.pipeline.use(ValidationMiddleware())

        # Initialize
        self._setup()

    def _setup(self) -> None:
        """Initialize modules and router aliases."""
        try:
            from pyregex.presentation.assistant.modules.catalog_module import CatalogModule
            from pyregex.domain.catalog.registry import catalog_registry
            self.catalog_registry = catalog_registry
        except ImportError:
            return
        
        # 0. Perform High-Performance Industrial Discovery (O(N) traversal, no file parsing)
        # (Lazy loaded when explicitly requested by user)

        # 1. Category Metadata Map (Common ones with icons/display)
        # In a full system, this could also be in YAML (category.yaml)
        category_meta = {
            "personal": ("🧑 Datos Personales", "🧑", "Personal, contacto, identidad"),
            "web": ("🌐 Web y Protocolos", "🌐", "URLs, HTTP, APIs, protocolos"),
            "finance": ("💰 Finanzas y Banca", "💰", "IBAN, SWIFT, tarjetas, facturas"),
            "security": ("🔒 Seguridad", "🔒", "AWS, API Keys, Tokens, Credenciales"),
            "devops": ("🚀 DevOps y Logs", "🚀", "Syslog, Docker, K8s, Terraform, Git"),
            "data": ("📊 Datos y Formatos", "📊", "JSON, XML, YAML, CSV, SQL"),
            "networking": ("📡 Redes", "📡", "IPv4/v6, MAC, Puertos, DNS"),
            "standards": ("📜 Estándares", "📜", "ISO, MIME, RFC, Semver"),
            "i18n": ("🌍 I18n", "🌍", "Códigos postales, locales, fechas"),
            "text": ("📝 Texto", "📝", "Markdown, LaTeX, Sentencias, Citas"),
            "science": ("🧪 Ciencia", "🧪", "Fórmulas, DNA, Unidades, DOI"),
            "programming": ("🐍 Programación", "🐍", "Python, JS, Java, Rust, Go"),
            "automotive": ("🚗 Automotriz", "🚗", "Matrículas, VIN, OBDII"),
            "healthcare": ("🏥 Salud", "🏥", "ICD-10, NDC, NPI, Vitales"),
            "legal": ("⚖️ Legal", "⚖️", "Citas, Leyes, Patentes, GDPR"),
            "communication": ("💬 Comunicación", "💬", "Telecomunicaciones, social, filtros"),
            "culture": ("🎨 Cultura", "🎨", "Música, arte, geografía"),
            "daily": ("🏡 Vida Diaria", "🏡", "Compras, hogar, hobbies"),
            "economy": ("📈 Economía", "📈", "Impuestos, contabilidad, mercados"),
            "health": ("🏥 Salud", "🏥", "Medicina, fitness, bienestar"),
            "industry": ("🏗️ Industria", "🏗️", "Construcción, logística, procesos"),
            "society": ("👥 Sociedad", "👥", "Política, leyes, demografía"),
            "technology": ("💻 Tecnología", "💻", "Hardware, software, AI"),
            "transport": ("🚗 Transporte", "🚗", "Vehículos, rutas, navegación"),
        }

        # 2. Discover @register_module'd classes (Manual modules)
        # This keeps compatibility with existing custom modules while we migrate
        self.registry.discover(self.cli)

        # 3. Register All Catalog Categories as Dynamic Modules
        # This is the "AHA" Discovery phase (Stock inventory)
        for cat_name in catalog_registry.list_categories():
            # If a manual module already registered this category, we might skip or merge.
            # For now, we only register if it's missing.
            if cat_name not in self.registry:
                display, icon, desc = category_meta.get(cat_name, (None, "🧩", ""))
                try:
                    dyn_mod = CatalogModule(cat_name, display, icon, desc, self.cli)
                    self.registry.register(dyn_mod)
                except Exception:
                    continue

        # 4. Setup standard aliases in the router
        self.router.setup_default_aliases()

        # Boot event
        self.events.emit_simple(EventType.SESSION_START, source="engine")

    # ── Public API ───────────────────────────────────────────────────

    def process_input(self, raw_input: str) -> PipelineResponse:
        """
        Main entry: process a single line of user input.

        Resolves the route, transitions the FSM, and dispatches
        to the appropriate handler.
        """
        self.session.record_command(raw_input)
        route = self.router.resolve(raw_input)

        request = PipelineRequest(
            command=route.type.name.lower(),
            args=[route.module, route.wizard, route.category, route.command],
            raw_input=raw_input,
            context={"route": route, "session": self.session},
        )

        # Context-aware resolution:
        # 1. Catalog Browsing (Folder/Entry matching)
        if self.fsm.state == SessionState.BROWSING_CATALOG:
            path = self.session.catalog_path
            subfolders, entries = self.catalog_registry.list_at_path(path)
            raw_stripped = raw_input.strip().lower()
            
            # Match subfolder precisely or by partial
            for f in subfolders:
                if raw_stripped == f.lower():
                    self.session.push_catalog(f)
                    return self._handle_catalog_path()
            
            # Match entry precisely
            for e in entries:
                if raw_stripped == e.lower():
                    # Map hierarchical path to domain module (first path element)
                    # e.g. path=['culture', 'literature'] -> module='culture'
                    target_module = path[0] if path else "catalog"
                    return self._handle_wizard(target_module, e)

        # 2. Module Context (In-module shortcuts/numbers)
        if self.session.current_module and self.fsm.state == SessionState.IN_MODULE:
            module_name = self.session.current_module
            resolved = self._resolve_in_module_context(raw_input.strip(), module_name)
            if resolved:
                return resolved

        return self.pipeline.execute(request, lambda req: self._dispatch(req, route))

    def _dispatch(self, request: PipelineRequest, route: Any) -> PipelineResponse:
        """Internal dispatcher based on route type."""

        if route.type == RouteType.EXIT:
            return PipelineResponse(success=True, result="exit")

        elif route.type == RouteType.BACK:
            self._handle_back()
            return PipelineResponse(success=True, result="back")

        elif route.type == RouteType.BUILTIN:
            return self._handle_builtin(route.command)

        elif route.type == RouteType.CATEGORY:
            return self._handle_category(route.category)

        elif route.type == RouteType.MODULE:
            return self._handle_module(route.module)

        elif route.type == RouteType.WIZARD:
            return self._handle_wizard(route.module, route.wizard)

        elif route.type == RouteType.CREATE:
            return self._handle_create()

        elif route.type == RouteType.MENU_SELECT:
            return self._handle_menu_select(route.command)

        elif route.type == RouteType.AMBIGUOUS:
            return PipelineResponse(
                success=True,
                result="ambiguous",
                warnings=[f"Multiple matches: {', '.join(route.suggestions)}"],
            )

        else:
            return PipelineResponse(
                success=False, error=f"Unknown command: {request.raw_input}"
            )

    # ── Handlers ─────────────────────────────────────────────────────

    def _handle_back(self) -> None:
        """Handle back navigation."""
        state = self.fsm.state
        if state == SessionState.BROWSING_CATALOG:
            if self.session.pop_catalog() is not None:
                # Still in catalog, just one level up
                return

        self.session.pop_nav()
        self.fsm.trigger("back")
        self.session.restore_state()

    def _handle_create(self) -> PipelineResponse:
        """Starts hierarchical catalog browsing."""
        self.session.clear_nav()
        self.session.clear_catalog()
        self.session.transition(SessionState.BROWSING_CATALOG)
        self.fsm.trigger("create") # Ensure FSM is in a browsing state
        return self._handle_catalog_path()

    def _handle_catalog_path(self) -> PipelineResponse:
        """Lists folders and entries at the current catalog path."""
        path = self.session.catalog_path
        subfolders, entries = self.catalog_registry.list_at_path(path)
        
        return PipelineResponse(
            success=True,
            result={
                "type": "catalog_path",
                "path": path,
                "subfolders": subfolders,
                "entries": entries
            }
        )

    def _handle_builtin(self, command: str) -> PipelineResponse:
        """Handle built-in commands."""
        if command == "help":
            return PipelineResponse(success=True, result="help")
        elif command == "history":
            return PipelineResponse(
                success=True,
                result="history",
                warnings=[str(e) for e in self.session.history[-10:]],
            )
        elif command == "clear":
            return PipelineResponse(success=True, result="clear")
        elif command == "status":
            return PipelineResponse(success=True, result=self.session.get_stats())
        elif command == "undo":
            snapshot = self.session.undo()
            return PipelineResponse(success=snapshot is not None, result=snapshot)
        elif command == "redo":
            snapshot = self.session.redo()
            return PipelineResponse(success=snapshot is not None, result=snapshot)
        return PipelineResponse(success=False, error=f"Unknown builtin: {command}")

    def _handle_category(self, category: str) -> PipelineResponse:
        """Navigate into a category."""
        self.session.push_nav(category)
        self.session.transition(SessionState.BROWSING)
        self.fsm.trigger("select_module", {"category": category})

        # Get modules in this category
        try:
            cat_enum = ModuleCategory(category)
            modules = self.registry.get_by_category(cat_enum)
            module_infos = [m.info for m in modules]
            return PipelineResponse(
                success=True, result={"category": category, "modules": module_infos}
            )
        except ValueError:
            return PipelineResponse(
                success=False, error=f"Unknown category: {category}"
            )

    def _handle_module(self, module_name: str) -> PipelineResponse:
        """Navigate into a module."""
        self.session.push_nav(module_name)
        self.session.current_module = module_name
        self.session.transition(SessionState.IN_MODULE)
        self.fsm.trigger("select_module", {"module": module_name})

        module = self.registry.get(module_name)
        wizards = module.get_wizards()

        return PipelineResponse(
            success=True,
            result={
                "module": module_name,
                "wizards": list(wizards.keys()),
                "info": module.info,
            },
        )

    def _handle_wizard(self, module_name: str, wizard_name: str) -> PipelineResponse:
        """Start a wizard."""
        self.session.push_nav(wizard_name)
        self.session.current_wizard = wizard_name
        self.session.transition(SessionState.IN_WIZARD)
        self.fsm.trigger("start_wizard", {"module": module_name, "wizard": wizard_name})

        self.events.emit_simple(
            EventType.WIZARD_START,
            source="engine",
            module=module_name,
            wizard=wizard_name,
        )

        try:
            module = self.registry.get(module_name)
            wizards = module.get_wizards()

            if wizard_name not in wizards:
                return PipelineResponse(
                    success=False,
                    error=f"Wizard '{wizard_name}' not found in module '{module_name}'",
                )

            wizard_cls = wizards[wizard_name]
            wizard = wizard_cls(self.cli, self.session)
            result = wizard.execute(self.session)

            if result.success and not result.cancelled:
                self.session.add_pattern(result)
                self.events.emit_simple(
                    EventType.WIZARD_COMPLETE,
                    source="engine",
                    pattern=result.pattern,
                    wizard=wizard_name,
                )
                self.fsm.trigger("preview")
                return PipelineResponse(success=True, result=result)
            elif result.cancelled:
                self.events.emit_simple(
                    EventType.WIZARD_CANCEL, source="engine", wizard=wizard_name
                )
                self.fsm.trigger("cancel")
                return PipelineResponse(success=True, result="cancelled")
            else:
                return PipelineResponse(success=False, error=result.error)

        except Exception as e:
            self.fsm.force_state(SessionState.ERROR)
            self.fsm.trigger("recover")
            return PipelineResponse(success=False, error=str(e))

    def _handle_menu_select(self, number: str) -> PipelineResponse:
        """Handle numeric menu selection — context-aware."""
        idx = int(number)
        state = self.fsm.state

        if state == SessionState.BROWSING_CATALOG:
            path = self.session.catalog_path
            subfolders, entries = self.catalog_registry.list_at_path(path)
            
            total = len(subfolders) + len(entries)
            if 1 <= idx <= total:
                if idx <= len(subfolders):
                    # Enter subfolder
                    self.session.push_catalog(subfolders[idx - 1])
                    return self._handle_catalog_path()
                else:
                    # Select wizard
                    entry_name = entries[idx - len(subfolders) - 1]
                    return self._handle_wizard("catalog", entry_name)
            else:
                return PipelineResponse(
                    success=False,
                    error=f"Opción {idx} fuera de rango (1-{total})",
                )

        current_module = self.session.current_module
        if current_module and state == SessionState.IN_MODULE:
            # Resolve number to wizard in current module
            module = self.registry.get(current_module)
            wizard_names = list(module.get_wizards().keys())
            if 1 <= idx <= len(wizard_names):
                wizard_name = wizard_names[idx - 1]
                return self._handle_wizard(current_module, wizard_name)
            else:
                return PipelineResponse(
                    success=False,
                    error=f"Opción {idx} fuera de rango (1-{len(wizard_names)})",
                )

        return PipelineResponse(
            success=True,
            result={"selection": idx},
            warnings=["Menu selection requires active context"],
        )

    def _resolve_in_module_context(self, text: str, module_name: str):
        """Try to resolve input as a wizard name within the current module."""
        text_lower = text.lower()
        try:
            module = self.registry.get(module_name)
            wizards = module.get_wizards()
            # Match by wizard display name (without _wizard suffix)
            for wiz_name in wizards:
                display = wiz_name.replace("_wizard", "")
                if text_lower == display or text_lower == wiz_name:
                    return self._handle_wizard(module_name, wiz_name)
            # Match by number
            if text_lower.isdigit():
                idx = int(text_lower)
                wizard_list = list(wizards.keys())
                if 1 <= idx <= len(wizard_list):
                    return self._handle_wizard(module_name, wizard_list[idx - 1])
        except Exception:
            pass
        return None

    # ── Stats & Info ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get comprehensive engine statistics."""
        return {
            "session": self.session.get_stats(),
            "modules": self.registry.count,
            "events": self.events.listener_count,
            "fsm_state": self.fsm.state.name,
            "timing": self._timing.get_stats(),
            "pipeline_log_entries": len(self._logging.log),
        }

    def shutdown(self) -> None:
        """Graceful shutdown."""
        self.events.emit_simple(EventType.SESSION_END, source="engine")
        self.events.clear()
        self.session.reset()
        self.fsm.reset()
