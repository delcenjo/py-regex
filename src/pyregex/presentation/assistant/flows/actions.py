"""Action-oriented interactive flows (Edit, History, Custom, Merge) for the PyRegex Assistant."""

from __future__ import annotations
import argparse
import re
import json
from typing import Any, Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from pyregex.domain.explain.engine import AdvancedExplainer
from pyregex.application.services.merge_service import RegexMergeService
from pyregex.application.services.editor_service import (
    RegexEditorService,
    HistoryManager,
)
from pyregex.domain.builders.base import RegexBuilder
from pyregex.domain.builders.generic import GenericBuilder
from pyregex.infrastructure.persistence.pattern_repository import SavedPattern
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n


class ActionFlows:
    """Handlers for action-oriented interactive assistant flows."""

    def __init__(self, cli: Any):
        self.cli = cli
        # For merge flow persistence in-session
        self._current_merged_pattern: Optional[str] = None

    def handle_edit_flow(
        self,
        initial_pattern: str,
        initial_flags: str = "",
        args: argparse.Namespace | None = None,
    ) -> tuple[str, str]:
        """Professional interactive regex editor wizard."""
        history = HistoryManager(initial_pattern, initial_flags)
        editor = RegexEditorService()

        # Define all available choices for autocompletion
        choices: list[str] = [
            "load",
            "inline",
            "replace",
            "flags",
            "group",
            "quant",
            "anchor",
            "escape",
            "optimize",
            "test",
            "history",
            "custom",
            "s",
        ]

        # If args provided, we might perform a single action and return, or start the loop.
        choice = self.cli._get_arg_or_prompt(args, "edit_subtype", "Edit >", choices)

        while True:
            current_p, current_f = history.get_current()

            # Show menu only in interactive mode
            if not args or not getattr(args, "edit_subtype", None):
                ansi.print_banner(i18n.t("edit_menu.title"))
                print(f"{ansi.label('Current:')} {ansi.regex_display(current_p)}")
                if current_f:
                    print(f"{ansi.label('Flags:')} {ansi.dim(current_f)}")
                for opt in choices[:-1]:
                    print(f" [{opt}] {i18n.t(f'edit_menu.{opt}')}")
                print(f" [s] {i18n.t('common.save')} & {i18n.t('common.back')}")

            if choice == "s" or not choice:
                return current_p or "", str(current_f) if current_f else ""

            if choice == "inline":
                new_p = self.cli._get_arg_or_prompt(
                    args, "new_pattern", "Edit: ", None, current_p
                ).strip()
                if new_p:
                    history.add(new_p, current_f)

            elif choice == "anchor":
                a_opts = ["start", "end", "both", "remove"]
                if not args or not getattr(args, "anchor_type", None):
                    print(f"\n{i18n.t('edit_menu.anchor_options.title')}")
                    for o in a_opts:
                        print(f" [{o}] {i18n.t(f'edit_menu.anchor_options.{o}')}")
                sub = self.cli._get_arg_or_prompt(
                    args, "anchor_type", ">", a_opts, "both"
                )
                if sub == "start":
                    history.add(
                        editor.add_anchors(current_p, start=True, end=False), current_f
                    )
                elif sub == "end":
                    history.add(
                        editor.add_anchors(current_p, start=False, end=True), current_f
                    )
                elif sub == "both":
                    history.add(
                        editor.add_anchors(current_p, start=True, end=True), current_f
                    )
                elif sub == "remove":
                    history.add(editor.remove_anchors(current_p), current_f)

            elif choice == "flags":
                f_opts = ["i", "m", "s", "x"]
                if not args or not getattr(args, "flags_type", None):
                    print(f"\n{i18n.t('edit_menu.flags_options.title')}")
                    print(f" Toggle flags: {', '.join(f_opts)}")
                sub = self.cli._get_arg_or_prompt(args, "flags_type", ">", f_opts)
                if sub in f_opts:
                    history.add(current_p, editor.toggle_flag(current_f, sub))

            elif choice == "group":
                g_opts = ["capture", "non_capture", "named", "optional"]
                if not args or not getattr(args, "group_type", None):
                    print(f"\n{i18n.t('edit_menu.group_options.title')}")
                    for o in g_opts:
                        print(f" [{o}] {i18n.t(f'edit_menu.group_options.{o}')}")
                sub = self.cli._get_arg_or_prompt(
                    args, "group_type", ">", g_opts, "capture"
                )
                if sub == "named":
                    name = self.cli._get_arg_or_prompt(
                        args, "group_name", f"{i18n.t('edit_menu.prompt.group_name')}: "
                    ).strip()
                    if name:
                        history.add(
                            editor.wrap_in_group(current_p, "named", name), current_f
                        )
                elif sub in g_opts:
                    history.add(editor.wrap_in_group(current_p, sub), current_f)

            elif choice == "replace":
                find_str = self.cli._get_arg_or_prompt(
                    args, "find_str", f"{i18n.t('edit_menu.prompt.find')}: "
                )
                replace_str = self.cli._get_arg_or_prompt(
                    args, "replace_str", f"{i18n.t('edit_menu.prompt.replace')}: "
                )
                if find_str and current_p:
                    history.add(current_p.replace(find_str, replace_str), current_f)

            elif choice == "optimize":
                history.add(editor.optimize(current_p), current_f)

            elif choice == "escape":
                e_opts = ["escape", "unescape"]
                if not args or not getattr(args, "escape_type", None):
                    print(f"\n{i18n.t('edit_menu.escape_options.title')}")
                sub = self.cli._get_arg_or_prompt(
                    args, "escape_type", ">", e_opts, "escape"
                )
                if sub == "escape":
                    history.add(editor.escape_text(current_p), current_f)
                elif sub == "unescape":
                    history.add(editor.unescape_text(current_p), current_f)

            elif choice == "quant":
                q_opts = ["exact", "range", "greedy", "lazy", "optional"]
                if not args or not getattr(args, "quant_type", None):
                    print(f"\n{i18n.t('edit_menu.quant_options.title')}")
                    for o in q_opts:
                        print(f" [{o}] {i18n.t(f'edit_menu.quant_options.{o}')}")
                sub = self.cli._get_arg_or_prompt(
                    args, "quant_type", ">", q_opts, "optional"
                )
                target = self.cli._get_arg_or_prompt(
                    args, "target", f"{i18n.t('edit_menu.prompt.target')} (e.g. +): "
                ).strip()
                if sub == "exact":
                    n = self.cli._get_arg_or_prompt(args, "n", "n: ").strip()
                    if n:
                        history.add(
                            editor.modify_quantifier(current_p, target, f"{{{n}}}"),
                            current_f,
                        )
                elif sub == "range":
                    m_min = self.cli._get_arg_or_prompt(args, "min", "min: ").strip()
                    m_max = self.cli._get_arg_or_prompt(args, "max", "max: ").strip()
                    if m_min:
                        history.add(
                            editor.modify_quantifier(
                                current_p, target, f"{{{m_min},{m_max}}}"
                            ),
                            current_f,
                        )
                elif sub == "lazy":
                    if target and not target.endswith("?"):
                        history.add(
                            editor.modify_quantifier(current_p, target, f"{target}?"),
                            current_f,
                        )
                elif sub == "optional":
                    history.add(
                        editor.modify_quantifier(current_p, target, "?"), current_f
                    )

            elif choice == "test":
                t_text = self.cli._get_arg_or_prompt(args, "test_text", "Test text: ")
                if current_p and re.search(current_p, t_text):
                    print(ansi.success("MATCH!"))
                else:
                    print(ansi.error("NO MATCH"))

            elif choice == "history":
                h_opts = ["undo", "redo", "list"]
                if not args or not getattr(args, "history_type", None):
                    print(f"\n{i18n.t('edit_menu.history_options.title')}")
                    for o in h_opts:
                        print(f" [{o}] {i18n.t(f'edit_menu.history_options.{o}')}")
                sub = self.cli._get_arg_or_prompt(
                    args, "history_type", ">", h_opts, "undo"
                )
                if sub == "undo":
                    res = history.undo()
                    if not res:
                        print(ansi.dim("No older history"))
                elif sub == "redo":
                    res = history.redo()
                    if not res:
                        print(ansi.dim("No newer history"))
                elif sub == "list":
                    for i, (p, f) in enumerate(history.list_history()):
                        curr = " -> " if i == history.index else "    "
                        print(
                            f"{curr}v{i}: {ansi.regex_display(p)} {ansi.dim(f'[{f}]' if f else '')}"
                        )

            elif choice == "custom":
                new_p = self.cli._get_arg_or_prompt(
                    args,
                    "new_pattern",
                    f"{i18n.t('edit_menu.prompt.custom')}: ",
                    None,
                    current_p,
                ).strip()
                if new_p:
                    history.add(new_p, current_f)

            # If we were in CLI mode, we break after one iteration
            if args and getattr(args, "edit_subtype", None):
                break

            choice = prompt("> ", completer=WordCompleter(choices)).strip().lower()
            if choice == "s" or not choice:
                break

        return history.get_current()

    def handle_hist_flow(self, args: argparse.Namespace | None = None) -> None:
        """Interactive management of saved patterns and history."""
        options = [
            "recent",
            "freq",
            "fav",
            "search",
            "collections",
            "stats",
            "export",
            "cleanup",
            "q",
        ]

        if not args or not getattr(args, "subtype", None):
            ansi.print_banner(i18n.t("hist_menu.title"))
            for opt in options:
                print(f" [{opt}] {i18n.t(f'hist_menu.{opt}')}")

        choice = self.cli._get_arg_or_prompt(args, "hist_subtype", "History >", options)
        if choice == "q" or not choice:
            return

        while True:
            if choice == "recent":
                recent = self.cli.history_repo.list_recent(10)
                for i, entry in enumerate(recent):
                    print(
                        f" {i + 1}. {ansi.regex_display(entry['pattern'])} {ansi.dim(f'({entry['command']})')}"
                    )

            elif choice == "freq":
                stats = self.cli.pattern_repo.get_stats()
                for i, p in enumerate(stats["most_used"]):
                    print(f" #{i + 1} {ansi.bold(p.name)} ({p.usage_count} uses)")

            elif choice == "fav":
                favs = [
                    p
                    for p in self.cli.pattern_repo.list_all(scope="private")
                    if p.is_favorite
                ]
                for p in favs:
                    print(f" ⭐ {ansi.bold(p.name)}: {ansi.regex_display(p.pattern)}")

            elif choice == "stats":
                stats = self.cli.pattern_repo.get_stats()
                print(f"\n{i18n.t('hist_menu.stats_labels.total')} {stats['total']}")
                print(
                    f"{i18n.t('hist_menu.stats_labels.favorites')} {stats['favorites']}"
                )
                print(f"{i18n.t('hist_menu.stats_labels.pinned')} {stats['pinned']}")
                print(
                    f"{i18n.t('hist_menu.stats_labels.collections')} {', '.join(stats['collections'])}"
                )

            elif choice == "search":
                term = self.cli._get_arg_or_prompt(
                    args, "term", f"{i18n.t('hist_menu.prompts.search')}: "
                ).strip()
                if term:
                    results = [
                        p
                        for p in self.cli.pattern_repo.list_all()
                        if term.lower() in p.name.lower()
                        or term.lower() in p.pattern.lower()
                    ]
                    for p in results:
                        print(
                            f" - {ansi.bold(p.name)}: {ansi.regex_display(p.pattern)}"
                        )

            elif choice == "collections":
                stats = self.cli.pattern_repo.get_stats()
                for col in stats["collections"]:
                    print(f" 📂 {col}")

            elif choice == "export":
                filename = self.cli._get_arg_or_prompt(
                    args,
                    "filename",
                    f"{i18n.t('hist_menu.prompts.filename')} (e.g. export.json): ",
                ).strip()
                if filename:
                    patterns = [
                        p.to_dict()
                        for p in self.cli.pattern_repo.list_all(scope="private")
                    ]
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(patterns, f, indent=2)
                    print(
                        ansi.success(f"Exported {len(patterns)} patterns to {filename}")
                    )

            elif choice == "cleanup":
                confirm = self.cli._get_arg_or_prompt(
                    args,
                    "confirm",
                    f"{i18n.t('hist_menu.prompts.confirm_delete')} (y/n): ",
                ).lower()
                if confirm == "y":
                    self.cli.history_repo.clear()
                    print(ansi.success("History cleared."))

            if args and getattr(args, "subtype", None):
                break

            choice = prompt("> ", completer=WordCompleter(options)).strip().lower()
            if choice == "q" or not choice:
                break

    def handle_custom_flow(
        self, args: argparse.Namespace | None = None
    ) -> tuple[Optional[RegexBuilder], list[str]]:
        """Professional interactive custom regex flow."""
        tags = ["manual"]
        explainer = AdvancedExplainer()

        options = ["new", "load", "edit", "test", "explain", "validate", "save", "q"]

        if not args or not getattr(args, "subtype", None):
            ansi.print_banner(i18n.t("custom_menu.title"))
            for opt in options:
                print(f" [{opt}] {i18n.t(f'custom_menu.{opt}')}")

        choice = self.cli._get_arg_or_prompt(
            args, "custom_subtype", "Custom >", options + ["q"]
        )
        if choice == "q" or not choice:
            return None, tags

        current_pattern = getattr(args, "pattern", "")

        while True:
            if not args or not getattr(args, "subtype", None):
                if current_pattern:
                    print(
                        f"\n{ansi.label('Current:')} {ansi.regex_display(current_pattern)}"
                    )

            if choice == "new":
                w_opts = ["wizard", "blank", "template"]
                if not args or not getattr(args, "custom_type", None):
                    print(f"\n{ansi.label(i18n.t('custom_menu.wizard_options.title'))}")
                    for o in w_opts:
                        print(f" [{o}] {i18n.t(f'custom_menu.wizard_options.{o}')}")
                sub = self.cli._get_arg_or_prompt(
                    args, "custom_type", ">", w_opts, "blank"
                )

                if sub == "wizard":
                    current_pattern = self.handle_custom_wizard(args)
                elif sub == "blank":
                    current_pattern = self.cli._get_arg_or_prompt(
                        args, "pattern", i18n.t("custom_menu.prompts.enter_regex")
                    )
                elif sub == "template":
                    current_pattern = (
                        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
                    )

            elif choice == "edit" and current_pattern:
                new_p, _ = self.handle_edit_flow(current_pattern)
                if new_p:
                    current_pattern = new_p

            elif choice == "explain" and current_pattern:
                res = explainer.explain(current_pattern)
                print(f"\n{ansi.bold(i18n.t('custom_menu.explain_options.title'))}")
                narrative = (
                    res["narrative"] if res.get("success") else [res.get("error")]
                )
                for line in narrative:
                    print(f"  {line}")

            elif choice == "validate" and current_pattern:
                try:
                    re.compile(current_pattern)
                    print(ansi.success(i18n.t("custom_menu.prompts.valid_regex")))
                except re.error as e:
                    print(
                        ansi.error(
                            i18n.t("custom_menu.prompts.invalid_regex", error=str(e))
                        )
                    )

            elif choice == "test" and current_pattern:
                test_text = self.cli._get_arg_or_prompt(
                    args, "test_text", "Test text: "
                )
                if re.search(current_pattern, test_text):
                    print(ansi.success("MATCH!"))
                else:
                    print(ansi.error("NO MATCH"))

            elif choice == "save" and current_pattern:
                name = self.cli._get_arg_or_prompt(
                    args, "name", "Enter name for this custom pattern: "
                )
                if name:
                    self.cli.pattern_repo.save(
                        SavedPattern(
                            name=name,
                            pattern=current_pattern,
                            description="Custom pattern created via manual input",
                            tags=tags,
                        )
                    )
                    print(ansi.success(f"Saved as {name}"))
                    return GenericBuilder({"id": name, "pattern": current_pattern}), tags

            if args and getattr(args, "subtype", None):
                return GenericBuilder(
                    {"id": "custom", "pattern": current_pattern}
                ) if current_pattern else None, tags

            choice = prompt("> ", completer=WordCompleter(options)).strip().lower()
            if choice == "q" or not choice:
                break

        return GenericBuilder({"id": "custom", "pattern": current_pattern}) if current_pattern else None, tags

    def handle_custom_wizard(self, args: argparse.Namespace | None = None) -> str:
        """Step-by-step wizard for creating common regex patterns."""
        ptype = (
            self.cli._get_arg_or_prompt(
                args, "wizard_type", f"{i18n.t('custom_menu.prompts.wizard_type')}: "
            )
            .strip()
            .lower()
        )

        if "email" in ptype:
            domain = self.cli._get_arg_or_prompt(
                args, "domain", "Specific domain (optional): "
            ).strip()
            if domain:
                return rf"\b[A-Za-z0-9._%+-]+@{re.escape(domain)}\b"
            return r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        elif "number" in ptype:
            digits = self.cli._get_arg_or_prompt(
                args, "digits", "Exact number of digits: "
            ).strip()
            if digits.isdigit():
                return rf"\d{{{digits}}}"
            return r"\d+"

        return self.cli._get_arg_or_prompt(
            args, "pattern", i18n.t("custom_menu.prompts.enter_regex")
        ).strip()

    def handle_merge_flow(
        self, args: argparse.Namespace | None = None
    ) -> tuple[Optional[RegexBuilder], list[str]]:
        """Professional interactive flow for merging multiple patterns."""
        selected_patterns: list[SavedPattern] = []
        merge_service = RegexMergeService()
        tags = ["merged"]

        options = ["select", "method", "grouping", "preview", "test", "save", "q"]

        if not args or not getattr(args, "subtype", None):
            ansi.print_banner(i18n.t("merge_menu.title"))
            for opt in options:
                print(f" [{opt}] {i18n.t(f'merge_menu.{opt}')}")

        choice = self.cli._get_arg_or_prompt(
            args, "merge_subtype", "Merge >", options + ["q"]
        )
        if choice == "q" or not choice:
            return None, tags

        while True:
            if not args or not getattr(args, "subtype", None):
                if selected_patterns:
                    print(f"\n{ansi.label('Selected:')}")
                    for i, p in enumerate(selected_patterns, 1):
                        print(
                            f"  {i}. {ansi.bold(p.name)}: {ansi.regex_display(p.pattern)}"
                        )

            if choice == "select":
                patterns = self.cli.pattern_repo.list_all()
                if not patterns:
                    print(ansi.error("No saved patterns found."))
                else:
                    if not args or not getattr(args, "indices", None):
                        print(f"\n{ansi.bold('Available Patterns:')}")
                        for i, p in enumerate(patterns, 1):
                            print(f"  {i}. {p.name} ({p.pattern})")

                    indices = self.cli._get_arg_or_prompt(
                        args, "indices", i18n.t("merge_menu.prompts.select_patterns")
                    )
                    try:
                        for idx in indices.split(","):
                            if idx.strip().isdigit():
                                selected_patterns.append(patterns[int(idx.strip()) - 1])
                    except (ValueError, IndexError):
                        print(ansi.error("Invalid selection."))

            elif choice == "method" and (
                selected_patterns or getattr(args, "indices", None)
            ):
                m_opts = ["or", "concat", "optional", "named_group"]
                if not args or not getattr(args, "method", None):
                    for o in m_opts:
                        print(f" [{o}] {i18n.t(f'merge_menu.methods.{o}')}")
                method = self.cli._get_arg_or_prompt(args, "method", ">", m_opts, "or")

                if method in m_opts or method == "trie":
                    raw_patterns = [p.pattern for p in selected_patterns]
                    if method == "named_group":
                        current_merged = merge_service.wrap_with_named_groups(
                            [(p.name, p.pattern) for p in selected_patterns]
                        )
                    elif method == "trie":
                        current_merged = merge_service.trie_merge(raw_patterns)
                    else:
                        current_merged = merge_service.merge(
                            raw_patterns, method=method
                        )

                    # Auto-optimize merged result
                    current_merged = merge_service.optimize_merged(current_merged)

                    print(f"\n{i18n.t('merge_menu.prompts.preview_title')}")
                    print(ansi.regex_display(current_merged))
                    self._current_merged_pattern = current_merged

            elif choice == "preview" and self._current_merged_pattern:
                print(f"\n{i18n.t('merge_menu.prompts.preview_title')}")
                print(ansi.regex_display(self._current_merged_pattern))

            elif choice == "test" and self._current_merged_pattern:
                test_text = self.cli._get_arg_or_prompt(
                    args, "test_text", "Test text: "
                )
                p = str(self._current_merged_pattern or "")
                matches = list(re.finditer(p, test_text))
                for match in matches:
                    print(
                        f"Match found: {ansi.success(match.group())} at {match.start()}-{match.end()}"
                    )
                if not matches:
                    print(ansi.error("No matches found."))

            elif choice == "save" and self._current_merged_pattern:
                name = self.cli._get_arg_or_prompt(
                    args, "name", i18n.t("merge_menu.prompts.merge_name")
                )
                if name:
                    self.cli.pattern_repo.save(
                        SavedPattern(
                            name=name,
                            pattern=self._current_merged_pattern,
                            description="Merged pattern",
                            tags=tags,
                        )
                    )
                    print(ansi.success(f"Saved as {name}"))
                    return GenericBuilder({"id": name, "pattern": self._current_merged_pattern}), tags

            if args and getattr(args, "subtype", None):
                return GenericBuilder(
                    {"id": "merged", "pattern": self._current_merged_pattern}
                ) if self._current_merged_pattern else None, tags

            choice = prompt("> ", completer=WordCompleter(options)).strip().lower()
            if choice == "q" or not choice:
                break

        return GenericBuilder(
            {"id": "merged", "pattern": self._current_merged_pattern}
        ) if self._current_merged_pattern else None, tags
