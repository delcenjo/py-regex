from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any
from tqdm import tqdm

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.application.services.audit.engine import AuditEngine
from pyregex.application.services.task_manager import TaskManager

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class AuditCommand(BaseCommand):
    """Audits files/directories for sensitive data patterns."""

    @property
    def name(self) -> str:
        return "audit"

    @property
    def help(self) -> str:
        return "Audit files/directories for sensitive data"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("path", help="The path to audit")
        parser.add_argument("--pii", action="store_true", help="Audit for PII")
        parser.add_argument("--secrets", action="store_true", help="Audit for secrets")
        parser.add_argument("--all", action="store_true", help="Audit for everything")
        parser.add_argument("--ignore-case", action="store_true", help="Ignore case")
        parser.add_argument("--exclude", help="Exclude pattern")
        parser.add_argument(
            "--resume", action="store_true", help="Resume previous audit"
        )
        parser.add_argument(
            "--parallel",
            nargs="?",
            type=int,
            const=0,
            default=None,
            help="Number of workers (0 for auto)",
        )
        parser.add_argument("--deep", action="store_true", help="Deep scan")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        path = Path(args.path)
        if not path.exists():
            print(ansi.error(f"Path not found: {args.path}"))
            return 1

        rules = []
        if args.pii:
            rules.append("PII")
        if args.secrets:
            rules.append("SECRETS")
        if args.all:
            rules.extend(["PII", "SECRETS"])
        if not rules:
            rules = ["all"]

        task_id = hashlib.md5(
            f"audit:{path}:{rules}:{args.exclude}".encode()
        ).hexdigest()
        tm = TaskManager(task_id)

        if args.resume and tm.get_pending():
            print(
                ansi.info(
                    f"Resuming task {task_id[:8]}... ({tm.progress:.1f}% complete)"
                )
            )
        elif not args.resume:
            tm.cleanup()
            tm = TaskManager(task_id)

        engine = AuditEngine(registry=cli.registry)

        max_workers = getattr(args, "parallel", None)

        files_to_scan = []
        try:
            files_to_scan = list(engine._iter_files(path))
        except AttributeError:
            files_to_scan = [path] if path.is_file() else []
            if path.is_dir():
                import os

                for root, _, filenames in os.walk(path):
                    for f in filenames:
                        files_to_scan.append(Path(root) / f)

        if max_workers is not None:
            import os

            if max_workers == 0:
                max_workers = os.cpu_count()
            if len(files_to_scan) <= 2:
                max_workers = None
            if args.resume:
                files_to_scan = [
                    f for f in files_to_scan if str(f) not in tm.completed_files
                ]
                tm.total_files = [str(f) for f in files_to_scan]

            print(ansi.info(f"Auditing path: {path}"))

            def on_file_processed(f_path):
                tm.mark_complete(f_path)
                pbar.update(1)

            with tqdm(
                total=len(files_to_scan),
                desc="🔍 Auditing",
                unit="file",
                disable=not files_to_scan,
            ) as pbar:
                results = engine.scan(
                    path=str(path),
                    rules=rules,
                    ignore_case=args.ignore_case,
                    exclude=args.exclude,
                    max_workers=max_workers,
                    deep=getattr(args, "deep", False),
                    progress_callback=on_file_processed if not max_workers else None,
                )
                if max_workers:
                    for f in files_to_scan:
                        tm.mark_complete(str(f))
                    pbar.update(len(files_to_scan))

            if tm.progress >= 100:
                tm.cleanup()
        else:
            # Fallback for sequential
            results = engine.scan(path=str(path), rules=rules)

        try:
            print(
                engine.render_detailed_report(
                    results, root_path=str(path) if path.is_dir() else ""
                )
            )
            return 0
        except Exception as e:
            print(ansi.error(f"Audit failed: {e}"))
            return 1
