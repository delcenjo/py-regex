"""Playground — Configuration."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PlaygroundConfig:
    """User-configurable playground settings."""

    # Theme
    theme: str = "dark"  # dark, light, monokai, solarized
    accent_color: str = "#00d4ff"

    # Layout
    layout: str = "default"  # default, compact, wide, vertical
    show_line_numbers: bool = True
    show_toolbar: bool = True
    show_header: bool = True
    wrap_lines: bool = True

    # Default visible panels
    default_panels: list[str] = field(
        default_factory=lambda: ["regex", "input", "matches", "stats"]
    )

    # Matching
    match_timeout_ms: int = 500  # max time for matching
    compile_timeout_ms: int = 100  # max time for compilation
    max_matches: int = 1000  # max matches to show
    max_input_size: int = 1_000_000  # max input text size (1MB)
    incremental_threshold: int = 10_000  # switch to incremental for large inputs

    # Performance
    enable_benchmarking: bool = True
    benchmark_iterations: int = 100
    enable_redos_detection: bool = True
    redos_timeout_ms: int = 2000

    # Debug
    max_debug_steps: int = 500

    # History
    max_history: int = 100
    auto_save: bool = True
    history_file: str = "~/.pyregex/playground_history.json"

    # Multi-language
    default_language: str = "python"
    available_languages: list[str] = field(
        default_factory=lambda: [
            "python",
            "javascript",
            "go",
            "java",
            "rust",
            "csharp",
            "php",
            "ruby",
        ]
    )

    # Highlighting colors (match groups)
    group_colors: list[str] = field(
        default_factory=lambda: [
            "#ff6b6b",
            "#ffd93d",
            "#6bcb77",
            "#4d96ff",
            "#ff922b",
            "#cc5de8",
            "#20c997",
            "#748ffc",
            "#f06595",
            "#a9e34b",
            "#3bc9db",
            "#ff8787",
        ]
    )

    # Sample data
    enable_sample_data: bool = True

    # ── File Mode ────────────────────────────────────────────────
    file_chunk_size: int = 64 * 1024  # 64KB read chunks
    file_max_preview_lines: int = 1000  # max lines shown in file panel
    file_context_lines: int = 2  # context lines around matches
    file_default_export: str = "json"  # json, csv, txt
    file_max_matches: int = 50_000  # max matches in file mode
    file_scroll_step: int = 10  # lines per scroll step
    file_export_dir: str = "~/pyregex_exports"  # default export dir

