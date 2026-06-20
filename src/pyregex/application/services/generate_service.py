import random
from typing import List, Optional
from pyregex.domain.builders.base import RegexBuilder


class SyntheticEngine:
    """Engine for generating synthetic data from regex builders or patterns.

    This is a key component for MLOps/DataEng workflows where realistic
    but fake datasets are needed for training and testing.
    """

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)

    def generate(
        self, builder: RegexBuilder, count: int = 1, config: Optional[dict] = None
    ) -> List[str]:
        """Generates N synthetic examples using a builder's own logic or metadata."""
        results = []

        if hasattr(builder, "generate"):
            for _ in range(count):
                results.append(builder.generate(config, self.rng))
            return results

        meta = builder.metadata
        if not meta.examples:
            pattern = builder.build_pattern()
            return [self._generate_from_pattern(pattern) for _ in range(count)]

        for _ in range(count):
            base = self.rng.choice(meta.examples)
            results.append(self._randomize_example(base, meta.category))

        return results

    def _randomize_example(self, example: str, category: str) -> str:
        """Slightly randomizes an existing example based on its category."""
        category = category.lower()

        if category == "web" and "@" in example:  # Email
            parts = example.split("@")
            return f"{parts[0]}{self.rng.randint(1, 999)}@{parts[1]}"

        if any(c.isdigit() for c in example):
            chars = list(example)
            for i, char in enumerate(chars):
                if char.isdigit() and self.rng.random() > 0.5:
                    chars[i] = str(self.rng.randint(0, 9))
            return "".join(chars)

        return example

    def _generate_from_pattern(self, pattern: str) -> str:
        """Generate a string that satisfies common regex constructs."""
        try:
            from re import _parser  # type: ignore
            return self._emit(_parser.parse(pattern))
        except Exception:
            return "".join(c for c in pattern if c.isalnum()) or "sample"

    def _emit(self, tokens) -> str:
        out = []
        for op, arg in tokens:
            name = getattr(op, "name", str(op)).upper()
            if name == "LITERAL":
                out.append(chr(arg))
            elif name == "ANY":
                out.append("x")
            elif name in ("MAX_REPEAT", "MIN_REPEAT"):
                low, _high, sub = arg
                out.append(self._emit(sub) * max(low, 1))
            elif name == "SUBPATTERN":
                out.append(self._emit(arg[-1]))
            elif name == "IN":
                out.append(self._emit_class(arg))
            elif name == "BRANCH":
                branches = arg[1]
                out.append(self._emit(branches[0]) if branches else "")
            elif name == "CATEGORY":
                out.append(self._category_char(getattr(arg, "name", str(arg))))
        return "".join(out)

    def _emit_class(self, items) -> str:
        for op, arg in items:
            name = getattr(op, "name", str(op)).upper()
            if name == "LITERAL":
                return chr(arg)
            if name == "RANGE":
                return chr(arg[0])
            if name == "CATEGORY":
                return self._category_char(getattr(arg, "name", str(arg)))
        return "x"

    @staticmethod
    def _category_char(category: str) -> str:
        category = category.upper()
        if "DIGIT" in category:
            return "5"
        if "SPACE" in category:
            return " "
        return "a"
