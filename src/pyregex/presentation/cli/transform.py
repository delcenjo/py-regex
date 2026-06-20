from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any
from tqdm import tqdm

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.application.services.transform_service import TransformEngine

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class TransformCommand(BaseCommand):
    """Applies a multi-rule transformation pipeline."""

    @property
    def name(self) -> str:
        return "transform"

    @property
    def help(self) -> str:
        return "Apply a transformation pipeline to files/directories"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("path", help="The path to transform")
        parser.add_argument(
            "--rules", required=True, help="Rules for transformation (rule:action,...)"
        )
        parser.add_argument("--output", help="The output path or directory")
        parser.add_argument(
            "--parallel", type=int, help="Number of workers (0 for auto)"
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        path = Path(args.path)
        if not path.exists():
            print(ansi.error(f"Path not found: {args.path}"))
            return 1

        engine = TransformEngine(registry=cli.registry)

        pipeline = []
        for rule_pair in args.rules.split(","):
            if ":" in rule_pair:
                r, a = rule_pair.split(":", 1)
                pipeline.append((r, a))
            else:
                pipeline.append((rule_pair, "mask"))

        max_workers = getattr(args, "parallel", None)

        files_to_transform = []
        try:
            files_to_transform = list(engine._iter_files(path))
        except AttributeError:
            files_to_transform = [path] if path.is_file() else []
            if path.is_dir():
                for root, _, filenames in os.walk(path):
                    for f in filenames:
                        files_to_transform.append(Path(root) / f)

        if max_workers is not None:
            if max_workers == 0:
                max_workers = os.cpu_count()
            if len(files_to_transform) <= 2:
                max_workers = None

        try:
            if path.is_file():
                count = engine.transform_file(
                    str(path), pipeline, output_path=args.output
                )
                print(
                    ansi.success(
                        f"Successfully transformed {path.name}. Items processed: {count}"
                    )
                )
            else:
                print(ansi.info(f"Transforming directory: {path}"))
                with tqdm(
                    total=len(files_to_transform),
                    desc="✨ Transforming",
                    unit="file",
                    disable=not files_to_transform,
                ) as pbar:
                    total, files = engine.transform_directory(
                        dirpath=str(path),
                        pipeline=pipeline,
                        output_dir=args.output,
                        max_workers=max_workers,
                        progress_callback=lambda: pbar.update(1),
                    )
                print(ansi.success(f"Successfully transformed directory {path.name}."))
                print(ansi.info(f"Files: {files}, Total items: {total}"))
            return 0
        except Exception as e:
            print(ansi.error(f"Transformation failed: {e}"))
            return 1
