"""Playground — Full-Screen TUI Application.

The main entry point for `px play` — a full-screen regex playground
built on prompt_toolkit with split panels, live highlighting, and
real-time matching.
"""

from __future__ import annotations
from typing import Optional
import re

from prompt_toolkit.application import Application
from prompt_toolkit.data_structures import Point
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl, FloatContainer, Float
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.margins import NumberedMargin
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.widgets import Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.filters import has_completions, Condition

from pyregex.presentation.playground.core.engine import PlaygroundEngine
from pyregex.presentation.playground.core.config import PlaygroundConfig
from pyregex.presentation.playground.regex.compiler import SafeCompiler
from pyregex.presentation.playground.regex.groups import GroupExtractor
from pyregex.presentation.playground.regex.optimizer import PatternOptimizer
from pyregex.presentation.playground.regex.debugger import StepDebugger
from pyregex.presentation.playground.regex.flags import FlagManager
from pyregex.presentation.playground.analysis.bridge import ExplainBridge
from pyregex.presentation.playground.multilang import MultiLangExporter
from pyregex.i18n import translator as i18n
from pyregex.presentation.playground.io import SAMPLES, CHEATSHEET
from pyregex.presentation.playground.alias.resolver import AliasResolver
from pyregex.presentation.playground.alias.completer import AliasCompleter
from pyregex.application.services.registry_controller import RegistryController


class PlaygroundApp:
    """
    Full-screen regex playground application.

    Layout:
    ┌────────────────────────────────────────────────────────┐
    │ 🎯 PyRegex Playground        Flags: [i] [m] [s] [x]  │
    ├────────────────────────────────────────────────────────┤
    │ REGEX:                                                 │
    │ > (editable regex input)                               │
    ├──────────────────────────┬─────────────────────────────┤
    │ INPUT:                   │ MATCHES:                    │
    │ (editable test text)     │ (match results)             │
    │                          ├─────────────────────────────┤
    │                          │ DETAILS:                    │
    │                          │ (groups/explain/debug)      │
    ├──────────────────────────┴─────────────────────────────┤
    │ ⚡ Stats  │  Keybindings                               │
    └────────────────────────────────────────────────────────┘
    """

    def __init__(
        self,
        config: Optional[PlaygroundConfig] = None,
        initial_regex: str = "",
        initial_input: str = "",
        registry: Optional[RegistryController] = None,
    ):
        self.config = config or PlaygroundConfig()
        self.engine = PlaygroundEngine(self.config)
        self.compiler = SafeCompiler()
        self.group_extractor = GroupExtractor()
        self.optimizer = PatternOptimizer()
        self.debugger = StepDebugger()
        self.flag_manager = FlagManager()
        self.explain_bridge = ExplainBridge()
        self.multilang = MultiLangExporter()

        # UI state
        self._detail_mode = "matches"
        self._show_help = False
        self._current_sample = -1
        self._expanded_view = False  # True = show raw regex, False = show @alias

        # Alias system
        self._registry = registry or RegistryController()
        self._alias_resolver = AliasResolver(self._registry)
        self._alias_completer = AliasCompleter(self._alias_resolver)

        self._matches_scroll: int = 0
        self._detail_scroll: int = 0

        self._matches_kb = self._build_matches_kb()
        self._detail_kb = self._build_detail_kb()

        # Content controls
        self._matches_content = FormattedTextControl(
            text="", 
            focusable=True, 
            key_bindings=self._matches_kb,
            get_cursor_position=lambda: Point(0, 0) if self._has_focus(self._matches_content) else None
        )
        self._detail_content = FormattedTextControl(
            text="", 
            focusable=True, 
            key_bindings=self._detail_kb,
            get_cursor_position=lambda: Point(0, 0) if self._has_focus(self._detail_content) else None
        )
        self._stats_content = FormattedTextControl(text="")
        self._header_content = FormattedTextControl(text=self._make_header())

        # Build buffers (callbacks may fire during text init)
        self._regex_buffer = Buffer(
            on_text_changed=self._on_regex_changed,
            multiline=False,
            completer=self._alias_completer,
            complete_while_typing=True,
        )
        self._input_buffer = Buffer(
            on_text_changed=self._on_input_changed,
            multiline=True,
        )
        self._replace_buffer = Buffer(
            on_text_changed=self._on_replace_changed,
            multiline=False,
        )

        # Build layout & app (before setting text so layout exists)
        self._kb = self._build_keybindings()
        self._layout = self._build_layout()
        self._style = self._build_style()
        self.app = Application(
            layout=Layout(self._layout),
            key_bindings=self._kb,
            style=self._style,
            full_screen=True,
            mouse_support=True,
        )

        # NOW set initial text (safe — all controls exist)
        if initial_regex:
            self._regex_buffer.text = initial_regex
        if initial_input:
            self._input_buffer.text = initial_input

        # Trigger initial computation
        self._on_regex_changed(self._regex_buffer)

    def _has_focus(self, control) -> bool:
        """Safely check if a control has focus."""
        if hasattr(self, 'app') and self.app is not None:
            return self.app.layout.has_focus(control)
        return False

    # ── Event handlers ────────────────────────────────────────────

    def _on_regex_changed(self, buffer: Buffer) -> None:
        """Called when regex text changes — recompute everything."""
        raw_pattern = buffer.text
        # Expand @aliases before passing to engine
        expanded = self._alias_resolver.expand(raw_pattern)
        self.engine.set_regex(expanded)
        self._update_all()

    def _on_input_changed(self, buffer: Buffer) -> None:
        """Called when input text changes — re-run matching."""
        self.engine.set_input(buffer.text)
        self._update_all()

    def _on_replace_changed(self, buffer: Buffer) -> None:
        """Called when replacement text changes."""
        self.engine.set_replace(buffer.text)
        self._update_detail()

    def _update_all(self) -> None:
        """Update all display panels."""
        self._update_matches()
        self._update_detail()
        self._update_stats()
        self._update_header()

    def _update_matches(self) -> None:
        """Update the matches panel."""
        state = self.engine.state
        lines: list[tuple[str, str]] = []

        if state.compile_error:
            lines.append(("class:error", f"  ❌ {state.compile_error}\n"))
        elif not state.regex_text:
            lines.append(("class:dim", f"  {i18n.t('playground.empty_regex', fallback='Escribe un regex arriba...')}\n"))
        elif not state.matches:
            lines.append(("class:warning", f"  {i18n.t('playground.no_matches', fallback='⚠️ Sin coincidencias')}\n"))
        else:
            lines.append(
                ("class:success", f"  {i18n.t('playground.matches_count', count=len(state.matches), fallback=f'✅ {len(state.matches)} coincidencia(s)')}\n\n")
            )
            for i, m in enumerate(state.matches[:50]):
                txt = m.text if len(m.text) <= 45 else m.text[:42] + "..."
                color = f"class:match{(i % 4) + 1}"
                lines.append((color, f"  {i + 1:2d}. "))
                lines.append(("class:match_text", f'"{txt}"'))
                lines.append(("class:dim", f"  pos {m.start}-{m.end}\n"))

                # Show groups inline
                if m.groups:
                    for gi, gv in enumerate(m.groups):
                        if gv is not None:
                            gv_short = gv if len(gv) <= 30 else gv[:27] + "..."
                            lines.append(("class:dim", f"      G{gi + 1}: "))
                            lines.append(("class:group_val", f'"{gv_short}"\n'))

            if len(state.matches) > 50:
                lines.append(
                    ("class:dim", f"\n  ... y {len(state.matches) - 50} más\n")
                )

        if self._matches_scroll > 0:
            lines = lines[self._matches_scroll:]

        self._matches_content.text = FormattedText(lines)

    def _update_detail(self) -> None:
        """Update the detail panel based on current mode."""
        lines: list[tuple[str, str]] = []
        state = self.engine.state

        if self._detail_mode == "groups":
            lines = self._render_groups()
        elif self._detail_mode == "explain":
            lines = self._render_explain()
        elif self._detail_mode == "debug":
            lines = self._render_debug()
        elif self._detail_mode == "replace":
            lines = self._render_replace()
        elif self._detail_mode == "cheatsheet":
            lines = [("class:cheatsheet", CHEATSHEET)]
        elif self._detail_mode == "export":
            lines = self._render_export()
        elif self._detail_mode == "optimize":
            lines = self._render_optimize()
        else:  # matches detail (default)
            if state.complexity.warnings:
                lines.append(("class:header", f"\n  {i18n.t('playground.warnings', fallback='⚠️ ADVERTENCIAS:')}\n"))
                for w in state.complexity.warnings:
                    lines.append(("class:warning", f"    • {w}\n"))
            if state.complexity.suggestions:
                lines.append(("class:header", f"\n  {i18n.t('playground.suggestions', fallback='💡 SUGERENCIAS:')}\n"))
                for s in state.complexity.suggestions:
                    lines.append(("class:info", f"    • {s}\n"))
            if not state.complexity.warnings and not state.complexity.suggestions:
                lines.append(("class:dim", f"  {i18n.t('playground.footer_hints', fallback='Tab entre paneles | F1-F7 para vistas')}\n"))

        if self._detail_scroll > 0:
            lines = lines[self._detail_scroll:]

        self._detail_content.text = FormattedText(lines)

    def _update_stats(self) -> None:
        """Update the stats bar."""
        state = self.engine.state
        perf = state.perf

        parts: list[tuple[str, str]] = []
        parts.append(("class:stats_icon", " ⚡ "))
        parts.append(("class:stats", f"{perf.total_time_us:.0f}μs "))
        parts.append(("class:stats_sep", "│ "))

        count = len(state.matches)
        if count > 0:
            parts.append(("class:stats_good", f"✓ {count} match "))
        elif state.compile_error:
            parts.append(("class:stats_bad", "✗ error "))
        else:
            parts.append(("class:stats_dim", "○ 0 match "))
        parts.append(("class:stats_sep", "│ "))

        # Complexity
        cx = state.complexity
        level_colors = {
            "low": "stats_good",
            "medium": "stats_warn",
            "high": "stats_bad",
            "critical": "stats_crit",
        }
        cx_style = f"class:{level_colors.get(cx.level, 'stats')}"
        filled = min(5, cx.score // 20)
        bar = "●" * filled + "○" * (5 - filled)
        parts.append((cx_style, f"{bar} {cx.level} "))
        parts.append(("class:stats_sep", "│ "))

        # Flags
        parts.append(("class:stats", f"Flags: {self.flag_manager.format_toolbar()} "))
        parts.append(("class:stats_sep", "│ "))

        # Mode
        parts.append(("class:stats_mode", f"[{self._detail_mode}] "))
        parts.append(("class:stats_sep", "│ "))

        # Keybinding hints
        msg = "Ctrl+Q salir │ Ctrl+J/K paneles │ Ctrl+E expandir │ Tab autocompletar"
        parts.append(("class:stats_dim", f" {msg} "))

        self._stats_content.text = FormattedText(parts)

    def _update_header(self) -> None:
        parts = [
            ("class:header_title", " 🎯 PyRegex Playground "),
            ("class:header_sep", " │ "),
            ("class:header_mode", f" Vista: {self._detail_mode.upper()} "),
            ("class:header_sep", " │ "),
            ("class:header_flags", f" {self.flag_manager.format_toolbar()} "),
        ]
        # Show alias expansion info if present
        raw = self._regex_buffer.text
        if self._alias_resolver.has_aliases(raw):
            expanded_display = self._alias_resolver.get_expanded_display(raw)
            parts.append(("class:header_sep", " │ "))
            parts.append(("class:header_alias", f" 🔗 {expanded_display} "))
        self._header_content.text = FormattedText(parts)

    def _make_header(self) -> FormattedText:
        return FormattedText(
            [
                ("class:header_title", " 🎯 PyRegex Playground "),
            ]
        )

    # ── Detail renderers ──────────────────────────────────────────

    def _render_groups(self) -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        state = self.engine.state
        table = self.group_extractor.extract(state.matches)
        if not table.has_groups:
            lines.append(("class:dim", f"  {i18n.t('playground.no_groups', fallback='Sin grupos de captura')}\n"))
            lines.append(("class:dim", f"  {i18n.t('playground.use_parens', fallback='Usa (...) para crear grupos')}\n"))
        else:
            for line in self.group_extractor.format_table(table):
                lines.append(("class:group_text", f"{line}\n"))
        return lines

    def _render_explain(self) -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        state = self.engine.state
        if not state.regex_text:
            lines.append(("class:dim", f"  {i18n.t('playground.explain_prompt', fallback='Escribe un regex para ver la explicación')}\n"))
        else:
            narrative = self.explain_bridge.get_narrative_text(state.regex_text)
            lines.append(("class:header", f"  {i18n.t('playground.explain_header', fallback='📖 EXPLICACIÓN:')}\n\n"))
            for n in narrative:
                n_str = str(n)
                lines.append(("class:explain_text", f"  {n_str}\n"))

            # Complexity badge
            badge = self.explain_bridge.get_complexity_badge(state.regex_text)
            lines.append(("", f"\n  Complejidad: {badge}\n"))
        return lines

    def _render_debug(self) -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        state = self.engine.state
        if not state.regex_text or not state.input_text:
            lines.append(("class:dim", f"  {i18n.t('playground.debug_prompt', fallback='Necesitas regex + texto para debug')}\n"))
        else:
            steps = self.debugger.debug(state.regex_text, state.input_text, state.flags)
            for step_line in self.debugger.format_debug(steps, verbose=True)[:100]:
                style = (
                    "class:debug_ok"
                    if "✅" in step_line or "✓" in step_line
                    else "class:debug_fail"
                )
                lines.append((style, f"{step_line}\n"))
        return lines

    def _render_replace(self) -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        state = self.engine.state
        ri = state.replace_info
        lines.append(("class:header", f"  {i18n.t('playground.replace_header', fallback='🔄 SUSTITUCIÓN:')}\n\n"))
        pat_str = self._replace_buffer.text or i18n.t('playground.replace_empty', fallback='(vacío)')
        lines.append(
            (
                "class:dim",
                f"  {i18n.t('playground.replace_pattern', pattern=pat_str, fallback=f'Patrón de reemplazo: {pat_str}')}\n",
            )
        )
        lines.append(("class:dim", f"  {i18n.t('playground.replace_count', count=ri.count, fallback=f'Sustituciones: {ri.count}')}\n\n"))
        if ri.result:
            lines.append(("class:replace_result", f"  {ri.result[:500]}\n"))
        return lines

    def _render_export(self) -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        state = self.engine.state
        if not state.regex_text:
            lines.append(("class:dim", f"  {i18n.t('playground.export_prompt', fallback='Escribe un regex para exportar')}\n"))
        else:
            outputs = self.multilang.export_all(state.regex_text, state.flags)
            for out in outputs:
                lines.append(
                    ("class:export_lang", f"\n  ── {out.language.upper()} ──\n")
                )
                for code_line in out.code.split("\n"):
                    lines.append(("class:export_code", f"  {code_line}\n"))
                if out.note:
                    lines.append(("class:warning", f"  {out.note}\n"))
        return lines

    def _render_optimize(self) -> list[tuple[str, str]]:
        lines: list[tuple[str, str]] = []
        state = self.engine.state
        if not state.regex_text:
            lines.append(("class:dim", f"  {i18n.t('playground.optimize_prompt', fallback='Escribe un regex para optimizar')}\n"))
        else:
            suggestions = self.optimizer.analyze(state.regex_text)
            for line in self.optimizer.format_suggestions(suggestions):
                lines.append(("class:optimize_text", f"{line}\n"))
        return lines

    # ── Layout ────────────────────────────────────────────────────

    def _build_layout(self):
        regex_area = Frame(
            Window(content=BufferControl(buffer=self._regex_buffer), height=1),
            title="REGEX",
            style="class:frame_regex",
        )

        input_area = Frame(
            Window(
                content=BufferControl(buffer=self._input_buffer), 
                wrap_lines=True,
                left_margins=[NumberedMargin()],
            ),
            title="INPUT",
            style="class:frame_input",
        )

        matches_area = Frame(
            Window(content=self._matches_content, wrap_lines=True),
            title="MATCHES",
            style="class:frame_matches",
        )

        detail_area = Frame(
            Window(content=self._detail_content, wrap_lines=True),
            title="DETALLE",
            style="class:frame_detail",
        )

        header = Window(
            content=self._header_content, height=1, style="class:header_bar"
        )

        stats_bar = Window(
            content=self._stats_content, height=1, style="class:stats_bar"
        )

        root_container = HSplit(
            [
                header,
                regex_area,
                VSplit(
                    [
                        input_area,
                        HSplit(
                            [
                                matches_area,
                                detail_area,
                            ]
                        ),
                    ],
                    padding=0,
                ),
                stats_bar,
            ]
        )

        # Wrap in FloatContainer with CompletionsMenu to render autocompletions
        return FloatContainer(
            content=root_container,
            floats=[
                Float(
                    xcursor=True,
                    ycursor=True,
                    content=CompletionsMenu(max_height=10, scroll_offset=1),
                )
            ]
        )

    # ── Keybindings ───────────────────────────────────────────────

    def _build_matches_kb(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("down")
        def _(e):
            self._matches_scroll += 1
            self._update_matches()

        @kb.add("up")
        def _(e):
            self._matches_scroll = max(0, self._matches_scroll - 1)
            self._update_matches()

        @kb.add("pagedown")
        def _(e):
            self._matches_scroll += 10
            self._update_matches()

        @kb.add("pageup")
        def _(e):
            self._matches_scroll = max(0, self._matches_scroll - 10)
            self._update_matches()

        @kb.add("home")
        def _(e):
            self._matches_scroll = 0
            self._update_matches()

        return kb

    def _build_detail_kb(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("down")
        def _(e):
            self._detail_scroll += 1
            self._update_detail()

        @kb.add("up")
        def _(e):
            self._detail_scroll = max(0, self._detail_scroll - 1)
            self._update_detail()

        @kb.add("pagedown")
        def _(e):
            self._detail_scroll += 10
            self._update_detail()

        @kb.add("pageup")
        def _(e):
            self._detail_scroll = max(0, self._detail_scroll - 10)
            self._update_detail()

        @kb.add("home")
        def _(e):
            self._detail_scroll = 0
            self._update_detail()

        return kb

    def _build_keybindings(self):
        kb = KeyBindings()

        @kb.add("c-q")
        def _(event):
            event.app.exit()

        @kb.add("c-c")
        def _(event):
            event.app.exit()

        @kb.add("escape")
        def _(event):
            event.app.exit()

        # Flag toggles
        @kb.add("c-i")
        def _(event):
            self.flag_manager.toggle(re.IGNORECASE)
            self.engine.state.flags = self.flag_manager.flags
            self._on_regex_changed(self._regex_buffer)

        @kb.add("c-o")
        def _(event):
            self.flag_manager.toggle(re.MULTILINE)
            self.engine.state.flags = self.flag_manager.flags
            self._on_regex_changed(self._regex_buffer)

        # Panel modes: F1-F7
        @kb.add("f1")
        def _(event):
            self._detail_mode = "cheatsheet"
            self._update_detail()
            self._update_stats()

        @kb.add("f2")
        def _(event):
            self._detail_mode = "groups"
            self._update_detail()
            self._update_stats()

        @kb.add("f3")
        def _(event):
            self._detail_mode = "explain"
            self._update_detail()
            self._update_stats()

        @kb.add("f4")
        def _(event):
            self._detail_mode = "debug"
            self._update_detail()
            self._update_stats()

        @kb.add("f5")
        def _(event):
            self._detail_mode = "replace"
            self._update_detail()
            self._update_stats()

        @kb.add("f6")
        def _(event):
            self._detail_mode = "export"
            self._update_detail()
            self._update_stats()

        @kb.add("f7")
        def _(event):
            self._detail_mode = "optimize"
            self._update_detail()
            self._update_stats()

        # Undo/redo
        @kb.add("c-z")
        def _(event):
            if self.engine.undo():
                self._regex_buffer.text = self.engine.state.regex_text
                self._input_buffer.text = self.engine.state.input_text

        @kb.add("c-y")
        def _(event):
            if self.engine.redo():
                self._regex_buffer.text = self.engine.state.regex_text
                self._input_buffer.text = self.engine.state.input_text

        # Load next/prev sample
        @kb.add("c-n")
        def _(event):
            if SAMPLES:
                self._current_sample = (self._current_sample + 1) % len(SAMPLES)
                s = SAMPLES[self._current_sample]
                self._regex_buffer.text = s.regex
                self._input_buffer.text = s.test_data

        @kb.add("c-p")
        def _(event):
            if SAMPLES:
                self._current_sample = (self._current_sample - 1) % len(SAMPLES)
                s = SAMPLES[self._current_sample]
                self._regex_buffer.text = s.regex
                self._input_buffer.text = s.test_data

        # ── Completion Menu Navigation (Priority) ────────────────
        @kb.add("tab", filter=has_completions)
        def _(event):
            event.current_buffer.complete_next()

        @kb.add("s-tab", filter=has_completions)
        def _(event):
            event.current_buffer.complete_previous()

        @kb.add("enter", filter=has_completions)
        def _(event):
            # Accept completion and close menu
            event.current_buffer.complete_state = None

        @kb.add("enter", filter=~has_completions & Condition(lambda: self.app.layout.current_buffer == self._input_buffer))
        def _(event):
            # Standard newline in multiline input
            event.current_buffer.insert_text("\n")

        # ── Panel navigation (All panels) ──
        @kb.add("c-j")
        def _(event):
            event.app.layout.focus_next()

        @kb.add("c-k")
        def _(event):
            event.app.layout.focus_previous()

        # Users can also switch panels using the mouse (mouse_support=True).

        # Alias expand/collapse toggle
        @kb.add("c-e")
        def _(event):
            raw = self._regex_buffer.text
            # Expand: replace @aliases and + compositions with real regex
            if self._alias_resolver.has_aliases(raw):
                expanded = self._alias_resolver.expand(raw)
                if expanded != raw:
                    self._regex_buffer.text = expanded
                    self._expanded_view = True

        return kb

    # ── Style ─────────────────────────────────────────────────────

    def _build_style(self):
        return Style.from_dict(
            {
                # Header
                "header_bar": "bg:#1a1a2e #e0e0e0",
                "header_title": "bg:#1a1a2e #00d4ff bold",
                "header_sep": "bg:#1a1a2e #555555",
                "header_mode": "bg:#1a1a2e #ffd93d",
                "header_flags": "bg:#1a1a2e #6bcb77",
                # Frames
                "frame_regex": "bg:#16213e",
                "frame_input": "bg:#0f3460",
                "frame_matches": "bg:#1a1a2e",
                "frame_detail": "bg:#1a1a2e",
                "frame_focused": "bg:#1a1a2e #00d4ff bold",
                # Stats bar
                "stats_bar": "bg:#0a0a1a #a0a0a0",
                "stats_icon": "bg:#0a0a1a #ffd93d",
                "stats": "bg:#0a0a1a #e0e0e0",
                "stats_sep": "bg:#0a0a1a #333333",
                "stats_good": "bg:#0a0a1a #6bcb77",
                "stats_bad": "bg:#0a0a1a #ff6b6b",
                "stats_crit": "bg:#0a0a1a #ff0000 bold",
                "stats_warn": "bg:#0a0a1a #ffd93d",
                "stats_dim": "bg:#0a0a1a #666666",
                "stats_mode": "bg:#0a0a1a #4d96ff bold",
                # Content
                "error": "#ff6b6b bold",
                "warning": "#ffd93d",
                "success": "#6bcb77 bold",
                "info": "#4d96ff",
                "dim": "#666666",
                "header": "#00d4ff bold",
                # Matches
                "match1": "#ff6b6b bold",
                "match2": "#ffd93d bold",
                "match3": "#6bcb77 bold",
                "match4": "#4d96ff bold",
                "match_text": "#ffffff",
                "group_val": "#cc5de8",
                "group_text": "#e0e0e0",
                # Detail panels
                "explain_text": "#e0e0e0",
                "debug_ok": "#6bcb77",
                "debug_fail": "#666666",
                "replace_result": "#20c997",
                "export_lang": "#00d4ff bold",
                "export_code": "#e0e0e0",
                "optimize_text": "#e0e0e0",
                "cheatsheet": "#a0a0a0",
            }
        )

    # ── Public API ────────────────────────────────────────────────

    def run(self) -> None:
        """Launch the playground."""
        self.app.run()

    def run_async(self):
        """Launch async."""
        return self.app.run_async()
