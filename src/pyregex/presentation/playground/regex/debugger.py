"""Playground — Step Debugger.

Shows how the regex engine processes text character by character.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import re


@dataclass
class DebugStep:
    """A single step in the regex matching process."""

    step_num: int
    text_pos: int  # position in input text
    pattern_pos: int  # position in pattern
    operation: str  # what's happening
    text_context: str  # surrounding text
    pattern_context: str  # surrounding pattern
    success: bool  # did this step succeed?
    group_state: dict[int, str] = field(default_factory=dict)  # current group captures

    @property
    def display(self) -> str:
        status = "" if self.success else ""
        return (
            f"[{self.step_num:3d}] {status} pos={self.text_pos:3d} | {self.operation}"
        )


class StepDebugger:
    """
    Debug regex matching step by step.

    Simulates the regex engine to show what happens at each position.
    Uses a simplified model since Python's re module doesn't expose
    internal matching state.
    """

    def __init__(self, max_steps: int = 500):
        self.max_steps = max_steps

    def debug(self, pattern_str: str, text: str, flags: int = 0) -> list[DebugStep]:
        """
        Generate debug steps for how the pattern matches against text.

        Uses a position-by-position approach to show what the engine
        tries at each location.
        """
        try:
            pattern = re.compile(pattern_str, flags)
        except re.error:
            return [
                DebugStep(
                    step_num=0,
                    text_pos=0,
                    pattern_pos=0,
                    operation="Error de compilación",
                    text_context="",
                    pattern_context=pattern_str,
                    success=False,
                )
            ]

        steps: list[DebugStep] = []
        step_num = 0

        # For each position in the text, try to match
        for pos in range(len(text) + 1):
            if step_num >= self.max_steps:
                steps.append(
                    DebugStep(
                        step_num=step_num,
                        text_pos=pos,
                        pattern_pos=0,
                        operation=f"Máximo de pasos alcanzado ({self.max_steps})",
                        text_context="...",
                        pattern_context="...",
                        success=False,
                    )
                )
                break

            # Get context around current position
            ctx_start = max(0, pos - 5)
            ctx_end = min(len(text), pos + 15)
            text_ctx = text[ctx_start:pos] + "▸" + text[pos:ctx_end]

            # Try to match at this position
            m = pattern.match(text, pos)

            if m:
                # Record successful match
                step_num += 1
                group_state = {}
                for i in range(pattern.groups + 1):
                    try:
                        g = m.group(i)
                        if g is not None:
                            group_state[i] = g
                    except IndexError:
                        pass

                steps.append(
                    DebugStep(
                        step_num=step_num,
                        text_pos=pos,
                        pattern_pos=0,
                        operation=f'Match: "{m.group()[:30]}" (len={m.end() - m.start()})',
                        text_context=text_ctx,
                        pattern_context=pattern_str,
                        success=True,
                        group_state=group_state,
                    )
                )

                # Show group captures
                for i in range(1, pattern.groups + 1):
                    try:
                        g = m.group(i)
                        if g is not None:
                            step_num += 1
                            name = None
                            for n, idx in pattern.groupindex.items():
                                if idx == i:
                                    name = n
                                    break
                            label = f"<{name}>" if name else f"#{i}"
                            steps.append(
                                DebugStep(
                                    step_num=step_num,
                                    text_pos=m.start(i),
                                    pattern_pos=0,
                                    operation=f'  Grupo {label} = "{g[:30]}"',
                                    text_context=text_ctx,
                                    pattern_context="",
                                    success=True,
                                )
                            )
                    except IndexError:
                        pass

                # Jump past this match
                if m.end() > pos:
                    pos_next = m.end() - 1  # will be incremented by loop
                continue
            else:
                # Record attempt at this position
                if pos < len(text):
                    step_num += 1
                    steps.append(
                        DebugStep(
                            step_num=step_num,
                            text_pos=pos,
                            pattern_pos=0,
                            operation=f"Probando en pos {pos} ('{text[pos]}'): sin match",
                            text_context=text_ctx,
                            pattern_context=pattern_str,
                            success=False,
                        )
                    )

        return steps

    def format_debug(self, steps: list[DebugStep], verbose: bool = False) -> list[str]:
        """Format debug steps as displayable lines."""
        lines = [
            "╔══════════════════════════════════════════╗",
            "║              DEBUG TRACE                 ║",
            "╚══════════════════════════════════════════╝",
            "",
        ]

        success_count = sum(1 for s in steps if s.success)
        fail_count = len(steps) - success_count
        lines.append(
            f"  Total: {len(steps)} pasos | {success_count} | {fail_count}"
        )
        lines.append("")

        for step in steps:
            lines.append(step.display)
            if verbose and step.text_context:
                lines.append(f"       Texto: {step.text_context}")
            if verbose and step.group_state:
                for gn, gv in step.group_state.items():
                    lines.append(f'       G{gn}: "{gv}"')

        return lines
