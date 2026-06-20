"""Playground File Mode — Full-Screen TUI Application.

Professional file-based regex playground launched via `px play --file <path>`.

Layout:
┌────────────────────────────────────────────────────────────┐
│ PyRegex File Mode │ access.log (2.1GB) │ UTF-8        │
├────────────────────────────────────────────────────────────┤
│ REGEX: (editable pattern)                                  │
├──────────────────────────────┬─────────────────────────────┤
│ FILE (scrollable):           │ MATCHES:                    │
│  1│ 192.168.1.1 ...          │  1. L:1  "192.168.1.1"     │
│ >5│ 172.16.0.1 ...           │  2. L:5  "172.16.0.1"      │
├──────────────────────────────┴─────────────────────────────┤
│ 2.3ms │ 847/125K │ F8 export │ Ctrl+Q salir            │
└────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import asyncio
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Point
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl, ConditionalContainer, FloatContainer, Float
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.widgets import Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.filters import Condition, has_completions

from pyregex.presentation.playground.core.config import PlaygroundConfig
from pyregex.presentation.playground.file.reader import FileReader
from pyregex.presentation.playground.file.scanner import FileScanner, ScanResult
from pyregex.presentation.playground.file.exporter import FileExporter, ExportOptions
from pyregex.presentation.playground.alias.resolver import AliasResolver
from pyregex.presentation.playground.alias.completer import AliasCompleter
from pyregex.application.services.registry_controller import RegistryController


class DynamicHeightControl(FormattedTextControl):
    """Fixed-text control that captures its actual rendered height."""
    def __init__(self, text, app_instance, attr_name="_visible_lines", **kwargs):
        super().__init__(text, **kwargs)
        self.app_instance = app_instance
        self.attr_name = attr_name

    def create_content(self, width, height):
        setattr(self.app_instance, self.attr_name, height)
        return super().create_content(width, height)


class FilePlaygroundApp:
    """Full-screen TUI for file-based regex matching.

    Features:
    - Live regex editing with instant re-scan
    - Scrollable file content with highlighted matches
    - Match list with line numbers and groups
    - Real-time statistics bar
    - Export matches (F8) — JSON, CSV, TXT, clipboard
    - Flag toggles, scroll navigation, go-to-line
    """

    def __init__(
        self,
        file_path: str,
        config: Optional[PlaygroundConfig] = None,
        initial_regex: str = "",
        initial_flags: int = 0,
        registry: Optional[RegistryController] = None,
    ):
        self.config = config or PlaygroundConfig()
        self._file_path = file_path

        self._reader = FileReader(file_path)
        self._file_info = self._reader.open()
        self._scanner = FileScanner(
            self._reader,
            max_matches=self.config.file_max_matches,
        )
        self._exporter = FileExporter(self._reader)

        self._flags: int = initial_flags
        self._scan_result: Optional[ScanResult] = None
        self._scroll_offset: int = 0  # file view top line (0-based)
        self._match_scroll: int = 0  # match list top index
        self._visible_lines: int = 20
        self._visible_matches: int = 20   # will be updated dynamically
        self._matched_line_set: set[int] = set()
        self._detail_mode: str = "matches"  # matches, groups, export
        self._export_msg: str = ""
        self._export_cycle: int = 0  # cycles through formats on F8
        self._base_memory_mb: float = self._get_memory_mb()

        self._wrap_lines: bool = False
        self._h_scroll: int = 0
        self._selected_line: int = 0
        self._focus_mode: bool = False
        self._expanded_view: bool = False

        self._registry = registry or RegistryController()
        self._alias_resolver = AliasResolver(self._registry)
        self._alias_completer = AliasCompleter(self._alias_resolver)

        self._scan_task: Optional[asyncio.Task] = None
        self._is_scanning: bool = False
        self._executor = ThreadPoolExecutor(max_workers=1)

        self._header_content = FormattedTextControl(text=" ")
        self._file_content = DynamicHeightControl(text=" ", app_instance=self, attr_name="_visible_lines",
            focusable=True,
            get_cursor_position=lambda: Point(0, 0) if self._has_focus(self._file_window) else None
        )
        self._matches_content = DynamicHeightControl(text=" ", app_instance=self, attr_name="_visible_matches",
            focusable=True,
            get_cursor_position=lambda: Point(0, 0) if self._has_focus(self._matches_window) else None
        )
        self._stats_content = FormattedTextControl(text="")
        self._focus_content = FormattedTextControl(text="")

        self._regex_buffer = Buffer(
            on_text_changed=self._on_regex_changed,
            multiline=False,
            completer=self._alias_completer,
            complete_while_typing=True,
        )

        self._regex_control = BufferControl(
            buffer=self._regex_buffer,
            focus_on_click=True,
        )
        self._file_window = Window(
            content=self._file_content,
            wrap_lines=Condition(lambda: self._wrap_lines),
        )
        self._matches_window = Window(
            content=self._matches_content,
            wrap_lines=True,
        )

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

        if initial_regex:
            self._regex_buffer.text = initial_regex

        self._update_header()
        self._update_file_view()
        self._update_stats()

    def _on_regex_changed(self, buffer: Buffer) -> None:
        """Cancel any pending scan and schedule a new one with debouncing."""
        if self._scan_task:
            self._scan_task.cancel()
        
        raw_pattern = buffer.text.strip()
        self._scan_task = self.app.create_background_task(
            self._debounced_scan(raw_pattern)
        )

    async def _debounced_scan(self, raw_pattern: str) -> None:
        """Wait for debounce period and run scan."""
        try:
            await asyncio.sleep(0.200)

            pattern = self._alias_resolver.expand(raw_pattern) if raw_pattern else ""

            if not pattern:
                self._scan_result = None
                self._matched_line_set = set()
                self._match_scroll = 0
                self._update_all()
                return

            self._update_all()

            self._is_scanning = True
            self._update_stats()
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor, 
                    self._scanner.scan, 
                    pattern, 
                    self._flags
                )
                
                self._scan_result = result
                self._matched_line_set = result.matched_lines
                self._match_scroll = 0
            except asyncio.CancelledError:
                raise
            except Exception:
                self._scan_result = None
                self._matched_line_set = set()
            finally:
                self._is_scanning = False
                self._update_all()

        except asyncio.CancelledError:
            pass

    def _update_all(self) -> None:
        self._update_header()
        self._update_file_view()
        self._update_matches()
        self._update_focus_view()
        self._update_stats()

    @staticmethod
    def _sanitize(text: str) -> str:
        """Remove ANSI escape sequences and control characters that break the TUI."""
        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]', '', text)
        return text

    def _update_file_view(self) -> None:
        """Render the scrollable file content with highlighted matches."""
        lines: list[tuple[str, str]] = []

        if not self._file_info or (self._reader.total_lines == 0 and self._reader.is_index_complete):
            lines.append(("class:dim", "  (archivo vacío)\n"))
            self._file_content.text = FormattedText(lines)
            return

        start = self._scroll_offset + 1
        end = min(
            self._scroll_offset + self._visible_lines,
            self._reader.total_lines,
        )

        compiled = None
        if self._regex_buffer.text.strip():
            try:
                compiled = re.compile(self._regex_buffer.text.strip(), self._flags)
            except re.error:
                compiled = None

        for line_no, raw_text in self._reader.get_lines(start, end):
            text = self._sanitize(raw_text)
            is_match = line_no in self._matched_line_set
            
            if not is_match and compiled:
                try:
                    if compiled.search(text):
                        is_match = True
                except Exception:
                    pass
            is_selected = (line_no == self._selected_line + 1)
            
            line_fragments: list[tuple[str, str]] = []

            if is_match and compiled:
                self._append_highlighted_line(line_fragments, text, compiled)
            else:
                style = "class:file_text" if not is_match else "class:file_match_line"
                if is_selected and self._has_focus(self._file_content):
                    style = "class:file_text_focused" if not is_match else "class:file_match_line_focused"
                # For non-wrapped performance, keep a long display string
                display = text[:1000] if len(text) > 1000 else text
                line_fragments.append((style, display))

            if self._h_scroll > 0 and not self._wrap_lines:
                line_fragments = self._slice_fragments(line_fragments, self._h_scroll)

            ln_style = "class:ln_match" if is_match else "class:ln"
            if is_selected:
                ln_style = "class:cursor_line_number"
            lines.append((ln_style, f" {line_no:6d} "))
            lines.append(("class:ln_sep", "│ "))

            for style, frag_text in line_fragments:
                if is_selected:
                    lines.append(("class:cursor_line", frag_text))
                else:
                    lines.append((style, frag_text))
                    
            lines.append(("", "\n"))

        total_lines = self._reader.total_lines
        if end < total_lines or not self._reader.is_index_complete:
            remaining_str = f"{total_lines - end:,} líneas más" if self._reader.is_index_complete else "Calculando líneas..."
            lines.append(("class:dim", f"\n  ↓ {remaining_str} (PgDn/↓)\n"))

        self._file_content.text = FormattedText(lines)

    def _slice_fragments(self, lines: list[tuple[str, str]], scroll_chars: int) -> list[tuple[str, str]]:
        if scroll_chars <= 0:
            return lines
        result = []
        dropped = 0
        for style, text in lines:
            if dropped < scroll_chars:
                if dropped + len(text) <= scroll_chars:
                    dropped += len(text)
                else:
                    keep = len(text) - (scroll_chars - dropped)
                    result.append((style, text[-keep:]))
                    dropped = scroll_chars
            else:
                result.append((style, text))
        return result

    def _append_highlighted_line(
        self, lines: list[tuple[str, str]], text: str, compiled: re.Pattern
    ) -> None:
        """Append a line with regex matches highlighted."""
        display = text[:1000] if len(text) > 1000 else text
        last_end = 0
        color_idx = 0
        colors = ["class:hl1", "class:hl2", "class:hl3", "class:hl4"]

        for m in compiled.finditer(display):
            if m.start() > last_end:
                lines.append(("class:file_text", display[last_end : m.start()]))
            style = colors[color_idx % len(colors)]
            lines.append((style, display[m.start() : m.end()]))
            color_idx += 1
            last_end = m.end()

        if last_end < len(display):
            lines.append(("class:file_text", display[last_end:]))
    def _update_matches(self) -> None:
        """Render the match list panel."""
        lines: list[tuple[str, str]] = []

        if self._export_msg:
            style = "class:error" if "" in self._export_msg else "class:success"
            lines.append((style, f"  {self._export_msg}\n"))
            lines.append(("class:dim", "  " + "─"*50 + "\n"))

        if self._scan_result is None:
            lines.append(("class:dim", "  Escribe un regex arriba...\n"))
        elif self._scan_result.match_count == 0:
            lines.append(("class:warning", "  Sin coincidencias\n"))
        else:
            sr = self._scan_result
            lines.append(
                ("class:success", f"  {sr.match_count:,} matches ")
            )
            lines.append(
                ("class:dim", f"en {sr.line_match_count:,}/{sr.total_lines:,} líneas\n\n")
            )

            visible = sr.matches[self._match_scroll : self._match_scroll + 100]
            for i, m in enumerate(visible):
                idx = self._match_scroll + i + 1
                sanitized_match = self._sanitize(m.match_text)
                txt = sanitized_match[:40] if len(sanitized_match) > 40 else sanitized_match
                color = f"class:match{(i % 4) + 1}"
                if self._has_focus(self._matches_content):
                    color = f"class:match{(i % 4) + 1}_focused"

                lines.append((color, f"  {idx:4d}. "))
                lines.append(("class:dim", f"L{m.line_no:<6d} "))
                lines.append(("class:match_text", f'"{txt}"'))
                lines.append(("class:dim", f"  [{m.start}:{m.end}]\n"))

                if m.groups:
                    for gi, gv in enumerate(m.groups):
                        if gv is not None:
                            sanitized_group = self._sanitize(str(gv))
                            gv_short = sanitized_group[:25] if len(sanitized_group) > 25 else sanitized_group
                            lines.append(("class:dim", f"         G{gi + 1}: "))
                            lines.append(("class:group_val", f'"{gv_short}"\n'))

            remaining = sr.match_count - self._match_scroll - len(visible)
            if remaining > 0:
                lines.append(("class:dim", f"\n  ... +{remaining:,} más\n"))

        self._matches_content.text = FormattedText(lines)

    def _update_focus_view(self) -> None:
        """Render the full raw text of the selected line."""
        if not self._focus_mode:
            self._focus_content.text = FormattedText([])
            return

        line_no = self._selected_line + 1
        raw_text = ""
        for _, text in self._reader.get_lines(line_no, line_no):
            raw_text = text
            break

        text = self._sanitize(raw_text)
        
        lines: list[tuple[str, str]] = []
        lines.append(("class:focus_header", f" Línea Completa {line_no:,} ".center(50, "─") + "\n\n"))
        
        compiled = None
        if self._regex_buffer.text.strip():
            try:
                compiled = re.compile(self._regex_buffer.text.strip(), self._flags)
            except re.error:
                pass
                
        fragments: list[tuple[str, str]] = []
        if compiled:
            self._append_highlighted_line(fragments, text, compiled)
        else:
            fragments.append(("class:file_text", text))
            
        lines.extend(fragments)
        self._focus_content.text = FormattedText(lines)

    def _update_header(self) -> None:
        fi = self._file_info
        parts: list[tuple[str, str]] = [
            ("class:header_title", " PyRegex File Mode "),
            ("class:header_sep", " │ "),
            ("class:header_file", f" {fi.path.split('/')[-1] if fi else '?'} "),
            ("class:header_sep", " │ "),
            ("class:header_size", f" {self._format_size(fi.size_bytes if fi else 0)} "),
            ("class:header_sep", " │ "),
            ("class:header_enc", f" {fi.encoding if fi else '?'} "),
            ("class:header_sep", " │ "),
        ]
        
        if self._reader.is_index_complete:
            parts.append(("class:header_lines", f" {self._reader.total_lines:,} líneas "))
        else:
            parts.append(("class:header_lines", f" ~{self._reader.total_lines:,}+ (Calculando...) "))
        flag_str = self._format_flags()
        if flag_str:
            parts.append(("class:header_sep", " │ "))
            parts.append(("class:header_flags", f" {flag_str} "))

        raw = self._regex_buffer.text
        if self._alias_resolver.has_aliases(raw):
            expanded_display = self._alias_resolver.get_expanded_display(raw)
            parts.append(("class:header_sep", " │ "))
            parts.append(("class:header_alias", f" {expanded_display} "))

        self._header_content.text = FormattedText(parts)

    def _update_stats(self) -> None:
        scan_time_ms = self._scan_result.scan_time_ms if self._scan_result else 0.0
        total_matches = self._scan_result.total_matches if self._scan_result else 0
        total_lines = self._scan_result.total_lines if self._scan_result else 0
        mem_mb = self._get_memory_mb()
        mem_delta_mb = mem_mb - self._base_memory_mb

        self._stats_content.text = FormattedText([
            ("class:stats_time", f" {scan_time_ms:>5.1f}ms " if not self._is_scanning else " ESCANEANDO... "),
            ("class:dim", " │ "),
            ("class:stats_count", f" {total_matches:,} matches in {total_lines:,} lines "),
            ("class:dim", " │ "),
            ("class:stats_mem", f" {mem_delta_mb:>+.1f}MB "),
            ("class:dim", " │ "),
            ("class:key", "C-j"), ("", " paneles "),
            ("class:dim", "│ "),
            ("class:key", "F8"), ("", " export "),
            ("class:dim", "│ "),
            ("class:key", "C-q"), ("", " salir "),
        ])

    def _has_focus(self, item) -> bool:
        """Robust focus check for either a Buffer, Window or Control."""
        if not self.app:
            return False
        return self.app.layout.has_focus(item)

    def _build_layout(self):
        header = Window(content=self._header_content, height=1, style="class:header_bar")

        regex_area = Frame(
            Window(content=self._regex_control, height=1),
            title="REGEX",
            style="class:frame_regex",
        )

        file_area = Frame(
            self._file_window,
            title="ARCHIVO",
            style="class:frame_file",
            width=Dimension(weight=1),
        )

        matches_area = Frame(
            self._matches_window,
            title="MATCHES",
            style="class:frame_matches",
            width=Dimension(weight=1),
        )

        stats_bar = Window(content=self._stats_content, height=1, style="class:stats_bar")

        focus_container = ConditionalContainer(
            content=Frame(
                Window(content=self._focus_content, wrap_lines=True),
                title="FOCUS LINE (Full Text)",
                style="class:frame_focus",
                height=Dimension(weight=30),
            ),
            filter=Condition(lambda: self._focus_mode)
        )

        main_split = VSplit([file_area, matches_area], padding=0)

        root_container = HSplit([
            header,
            regex_area,
            main_split,
            focus_container,
            stats_bar,
        ])

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

    def _build_keybindings(self):
        kb = KeyBindings()

        @kb.add("c-c")
        @kb.add("c-q")
        @kb.add("escape")
        def _(event):
            self._reader.close()
            event.app.exit()

        @kb.add("c-j")
        def _(event):
            # cycle: Regex -> File -> Matches
            if self._has_focus(self._regex_buffer):
                event.app.layout.focus(self._file_window)
            elif self._has_focus(self._file_window):
                event.app.layout.focus(self._matches_window)
            else:
                event.app.layout.focus(self._regex_buffer)

        @kb.add("c-k")
        def _(event):
            # reverse cycle: Matches -> File -> Regex
            if self._has_focus(self._regex_buffer):
                event.app.layout.focus(self._matches_window)
            elif self._has_focus(self._matches_window):
                event.app.layout.focus(self._file_window)
            else:
                event.app.layout.focus(self._regex_buffer)

        file_focused = Condition(lambda: self._has_focus(self._file_window))

        @kb.add("down", filter=file_focused & ~has_completions)
        @kb.add("j", filter=file_focused & ~has_completions)
        def _(event):
            max_line = max(0, self._reader.total_lines - 1)
            self._selected_line = min(self._selected_line + 1, max_line)
            if self._selected_line >= self._scroll_offset + self._visible_lines - 2:
                max_off = max(0, self._reader.total_lines - self._visible_lines)
                self._scroll_offset = min(self._scroll_offset + 1, max_off)
            self._update_all()

        @kb.add("up", filter=file_focused & ~has_completions)
        @kb.add("k", filter=file_focused & ~has_completions)
        def _(event):
            self._selected_line = max(0, self._selected_line - 1)
            if self._selected_line < self._scroll_offset + 5:
                self._scroll_offset = max(0, self._scroll_offset - 1)
            self._update_all()

        @kb.add("right", filter=file_focused & ~has_completions)
        def _(event):
            self._h_scroll += 10
            self._update_all()

        @kb.add("left", filter=file_focused & ~has_completions)
        def _(event):
            self._h_scroll = max(0, self._h_scroll - 10)
            self._update_all()

        @kb.add("pagedown", filter=file_focused & ~has_completions)
        def _(event):
            step = 20
            max_line = max(0, self._reader.total_lines - 1)
            self._selected_line = min(self._selected_line + step, max_line)
            self._scroll_offset = min(self._scroll_offset + step, max(0, self._reader.total_lines - self._visible_lines))
            self._update_all()

        @kb.add("pageup", filter=file_focused & ~has_completions)
        def _(event):
            step = 20
            self._selected_line = max(0, self._selected_line - step)
            self._scroll_offset = max(0, self._scroll_offset - step)
            self._update_all()

        @kb.add("home", filter=file_focused & ~has_completions)
        def _(event):
            self._scroll_offset = 0
            self._selected_line = 0
            self._update_all()

        @kb.add("end", filter=file_focused & ~has_completions)
        def _(event):
            max_line = max(0, self._reader.total_lines - 1)
            self._selected_line = max_line
            self._scroll_offset = max(0, self._reader.total_lines - self._visible_lines)
            self._update_all()

        matches_focused = Condition(lambda: self._has_focus(self._matches_window))

        @kb.add("down", filter=matches_focused & ~has_completions)
        @kb.add("j", filter=matches_focused & ~has_completions)
        def _(event):
            if self._scan_result:
                max_scroll = max(0, self._scan_result.match_count - 1)
                self._match_scroll = min(self._match_scroll + 1, max_scroll)
                self._update_matches()

        @kb.add("up", filter=matches_focused & ~has_completions)
        @kb.add("k", filter=matches_focused & ~has_completions)
        def _(event):
            self._match_scroll = max(0, self._match_scroll - 1)
            self._update_matches()

        @kb.add("pagedown", filter=matches_focused & ~has_completions)
        def _(event):
            if self._scan_result:
                self._match_scroll = min(self._match_scroll + 10, max(0, self._scan_result.match_count - 1))
                self._update_matches()

        @kb.add("pageup", filter=matches_focused & ~has_completions)
        def _(event):
            self._match_scroll = max(0, self._match_scroll - 10)
            self._update_matches()

        @kb.add("home", filter=matches_focused & ~has_completions)
        def _(event):
            self._match_scroll = 0
            self._update_matches()

        @kb.add("end", filter=matches_focused & ~has_completions)
        def _(event):
            if self._scan_result:
                self._match_scroll = max(0, self._scan_result.match_count - 1)
                self._update_matches()

        @kb.add("c-i")
        def _(event):
            self._flags ^= re.IGNORECASE
            self._on_regex_changed(self._regex_buffer)

        @kb.add("c-m")
        def _(event):
            self._flags ^= re.MULTILINE
            self._on_regex_changed(self._regex_buffer)

        @kb.add("c-s")
        def _(event):
            self._flags ^= re.DOTALL
            self._on_regex_changed(self._regex_buffer)

        @kb.add("c-w")
        def _(event):
            self._wrap_lines = not self._wrap_lines
            self._update_all()

        @kb.add("f4")
        @kb.add("enter", filter=~Condition(lambda: self.app.layout.has_focus(self._regex_buffer)))
        def _(event):
            self._focus_mode = not self._focus_mode
            self._update_all()

        @kb.add("f8")
        @kb.add("c-o")
        def _(event):
            if self._scan_result:
                self._run_export_menu()

        @kb.add("c-e")
        def _(event):
            raw = self._regex_buffer.text
            if self._alias_resolver.has_aliases(raw):
                self._regex_buffer.text = self._alias_resolver.expand(raw)
                self._on_regex_changed(self._regex_buffer)

        @kb.add("tab", filter=has_completions)
        def _(event):
            event.current_buffer.complete_next()

        @kb.add("s-tab", filter=has_completions)
        def _(event):
            event.current_buffer.complete_previous()

        @kb.add("enter", filter=has_completions)
        def _(event):
            event.current_buffer.complete_state = None

        return kb

    def _run_export_menu(self) -> None:
        """Cycle through export formats: JSON → CSV → TXT → Clipboard."""
        formats = ["json", "csv", "txt", "clipboard"]
        sr = self._scan_result
        if not sr:
            return

        fmt = formats[self._export_cycle % len(formats)]
        self._export_cycle += 1

        export_dir = self.config.file_export_dir or "~/pyregex_exports"
        src_dir = Path(export_dir).expanduser().resolve()
        
        try:
            os.makedirs(src_dir, exist_ok=True)
        except OSError:
            src_dir = Path.cwd()

        base = Path(self._file_path).stem
        ext_map = {"json": ".json", "csv": ".csv", "txt": ".txt"}

        try:
            if fmt == "clipboard":
                self._exporter.export(
                    sr, ExportOptions(format="clipboard", include_groups=True)
                )
                self._export_msg = (
                    f"{sr.match_count:,} matches → portapapeles "
                    f"(Repetir para sig. formato)"
                )
            else:
                out_path = str(src_dir / f"{base}_matches{ext_map[fmt]}")
                output = self._exporter.export(
                    sr,
                    ExportOptions(
                        format=fmt,
                        output_path=out_path,
                        include_groups=True,
                        include_context=True,
                        context_lines=self.config.file_context_lines,
                    ),
                )
                self._export_msg = (
                    f"{fmt.upper()}: {out_path} "
                    f"({len(output):,} bytes) — Repetir para sig."
                )
        except Exception as e:
            self._export_msg = f"Error exportando: {e}"

        self._update_matches()

    def _format_flags(self) -> str:
        parts = []
        if self._flags & re.IGNORECASE:
            parts.append("[i]")
        if self._flags & re.MULTILINE:
            parts.append("[m]")
        if self._flags & re.DOTALL:
            parts.append("[s]")
        return " ".join(parts) if parts else ""

    @staticmethod
    def _get_memory_mb() -> float:
        """Return current process RSS in MB.

        Reads /proc/self/status on Linux; falls back to the resource module
        on other Unix systems; returns 0.0 if neither is available.
        """
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        return kb / 1024.0
        except (FileNotFoundError, ValueError, IndexError):
            pass

        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            import sys
            if sys.platform == "darwin":
                return usage.ru_maxrss / (1024 * 1024)
            return usage.ru_maxrss / 1024
        except (ImportError, Exception):
            return 0.0

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f}{unit}" if unit != "B" else f"{size}{unit}"
            size = size / 1024  # type: ignore
        return f"{size:.1f}TB"

    def _build_style(self):
        return Style.from_dict({
            "header_bar": "bg:#1a1a2e #e0e0e0",
            "header_title": "bg:#1a1a2e #00d4ff bold",
            "header_sep": "bg:#1a1a2e #444",
            "header_file": "bg:#1a1a2e #ffd93d bold",
            "header_size": "bg:#1a1a2e #6bcb77",
            "header_enc": "bg:#1a1a2e #cc5de8",
            "header_lines": "bg:#1a1a2e #4d96ff",
            "header_flags": "bg:#1a1a2e #ff922b",
            "frame_regex": "bg:#16213e",
            "frame_file": "bg:#0f1923",
            "frame_matches": "bg:#1a1a2e",
            "frame_focused": "bg:#1a1a2e #00d4ff bold",
            "ln": "#555",
            "ln_match": "#ffd93d bold",
            "file_text": "#c0c0c0",
            "file_match_line": "#e0e0e0",
            "file_text_focused": "bg:#0a1a2a #ffffff",
            "file_match_line_focused": "bg:#0a1a2a #ffd93d bold",
            "match1_focused": "bg:#0a1a2a #ff6b6b bold",
            "match2_focused": "bg:#0a1a2a #ffd93d bold",
            "match3_focused": "bg:#0a1a2a #6bcb77 bold",
            "match4_focused": "bg:#0a1a2a #4d96ff bold",
            "hl1": "#1a1a2e bg:#ff6b6b bold",
            "hl2": "#1a1a2e bg:#ffd93d bold",
            "hl3": "#1a1a2e bg:#6bcb77 bold",
            "hl4": "#1a1a2e bg:#4d96ff bold",
            "match1": "#ff6b6b bold",
            "match2": "#ffd93d bold",
            "match3": "#6bcb77 bold",
            "match4": "#4d96ff bold",
            "match_text": "#fff",
            "group_val": "#cc5de8",
            "stats_bar": "bg:#0a0a1a #a0a0a0",
            "stats_icon": "bg:#0a0a1a #ffd93d",
            "stats": "bg:#0a0a1a #e0e0e0",
            "stats_sep": "bg:#0a0a1a #333",
            "stats_good": "bg:#0a0a1a #6bcb77 bold",
            "stats_warn": "bg:#0a0a1a #ffd93d bold",
            "stats_bad": "bg:#0a0a1a #ff6b6b bold",
            "stats_dim": "bg:#0a0a1a #666",
            "success": "#6bcb77 bold",
            "warning": "#ffd93d",
            "dim": "#666",
            "error": "#ff6b6b bold",
        })

    def run(self) -> None:
        """Launch the file playground."""
        try:
            self.app.run()
        finally:
            self._reader.close()
