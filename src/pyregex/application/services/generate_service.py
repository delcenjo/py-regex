import random
import hashlib
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

        # Priority 1: Use builder's specialized generator if it exists (future proofing)
        if hasattr(builder, "generate"):
            for _ in range(count):
                results.append(builder.generate(config, self.rng))
            return results

        # Priority 2: Use metadata examples and mutate/randomize them
        meta = builder.metadata
        if not meta.examples:
            # Fallback to very basic pattern-based generation if no examples
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
            # Replace some digits with other digits
            chars = list(example)
            for i, char in enumerate(chars):
                if char.isdigit() and self.rng.random() > 0.5:
                    chars[i] = str(self.rng.randint(0, 9))
            return "".join(chars)

        return example

    def _generate_from_pattern(self, pattern: str) -> str:
        """Very basic fallback generator for common regex constructs."""
        # This is a placeholder for a more complex regex-to-string engine.
        # For now, we return a warning or a very simple string.
        return f"synthetic_match_for_{hashlib.md5(pattern.encode()).hexdigest()[:8]}"
