from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Any
from tqdm import tqdm

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.application.services.mask.engine import MaskEngine
from pyregex.application.services.task_manager import TaskManager

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class MaskCommand(BaseCommand):
    """Anonymizes sensitive data using the MaskEngine."""

    @property
    def name(self) -> str:
        return "mask"

    @property
    def help(self) -> str:
        return "Mask sensitive data in files/directories"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "target_args",
            nargs="+",
            help="Types to mask (optional) followed by the file/dir path",
        )
        parser.add_argument(
            "--mode", default="hash", help="Masking mode (hash, mask, replace)"
        )
        parser.add_argument("--salt", help="Salt for hashing")
        parser.add_argument(
            "--types", nargs="+", help="Additional types to mask (e.g. email, phone)"
        )
        parser.add_argument("--rules", help="Rules separated by comma")
        parser.add_argument(
            "--inplace", action="store_true", help="Modify files in place"
        )
        parser.add_argument("--dry-run", action="store_true", help="Dry run")
        parser.add_argument("--ignore-case", action="store_true", help="Ignore case")
        parser.add_argument("--exclude", help="Exclude pattern")
        parser.add_argument(
            "--resume", action="store_true", help="Resume previous masking"
        )
        parser.add_argument(
            "--parallel", type=int, help="Number of workers (0 for auto)"
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        if len(args.target_args) >= 2:
            extracted_types = args.target_args[:-1]
            target_path_str = args.target_args[-1]
        else:
            extracted_types = []
            target_path_str = args.target_args[0]

        path = Path(target_path_str)
        if not path.exists():
            print(ansi.error(f"Path not found: {target_path_str}"))
            return 1

        salt = getattr(args, "salt", None) or getattr(cli.config, "salt", "pyregex2026")

        engine = MaskEngine(mode=args.mode, salt=salt, registry=cli.registry)
        rules = []
        if extracted_types:
            rules.extend(extracted_types)
        if args.types:
            rules.extend(args.types)
        if hasattr(args, "rules") and args.rules:
            rules.extend(args.rules.split(","))
        if not rules:
            rules = ["pii"]

        max_workers = getattr(args, "parallel", None)

        files_to_mask = []
        try:
            files_to_mask = list(engine._iter_files(path))
        except AttributeError:
            files_to_mask = [path] if path.is_file() else []
            if path.is_dir():
                import os

                for root, _, filenames in os.walk(path):
                    for f in filenames:
                        files_to_mask.append(Path(root) / f)

        if max_workers is not None:
            import os

            if max_workers == 0:
                max_workers = os.cpu_count()
            if len(files_to_mask) <= 2:
                max_workers = None

        try:
            task_id = hashlib.md5(
                f"mask:{path}:{rules}:{args.mode}:{salt}".encode()
            ).hexdigest()
            tm = TaskManager(task_id)

            skip_list = []
            if args.resume:
                skip_list = list(tm.completed_files)
                if skip_list:
                    print(
                        ansi.info(
                            f"Resuming task {task_id[:8]}... ({tm.progress:.1f}% complete)"
                        )
                    )
            else:
                tm.cleanup()
                tm = TaskManager(task_id)

            print(ansi.info(f"Masking path: {path}"))

            def on_file_done(f_path):
                tm.mark_complete(f_path)
                pbar.update(1)

            with tqdm(
                total=len(files_to_mask),
                desc="Masking",
                unit="file",
                disable=not files_to_mask,
            ) as pbar:
                if args.resume:
                    pbar.update(len(skip_list))
                total_m, files_m = engine.mask_directory(
                    str(path),
                    rules,
                    inplace=args.inplace,
                    dry_run=args.dry_run,
                    ignore_case=args.ignore_case,
                    exclude=args.exclude,
                    max_workers=max_workers,
                    progress_callback=on_file_done,
                    skip_files=skip_list,
                )

            if tm.progress >= 100:
                tm.cleanup()
                print(ansi.success(f"Successfully processed directory {path.name}."))
                print(
                    ansi.info(
                        f"Files modified: {files_m}, Total matches masked: {total_m}"
                    )
                )
            return 0
        except Exception as e:
            print(ansi.error(f"Masking failed: {e}"))
            return 1
