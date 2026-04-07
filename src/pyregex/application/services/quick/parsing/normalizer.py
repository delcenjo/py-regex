import re
import unicodedata
from pyregex.application.services.quick.base import QuickModule


class Normalizer(QuickModule):
    """Normalizes input text for better tokenization and matching."""

    def normalize(self, text: str) -> str:
        # Case folding
        text = text.lower()
        # Remove accents/diacritics
        text = "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        # Remove non-alphanumeric (except space)
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text


class Tokenizer(QuickModule):
    """Splits normalized text into searchable tokens."""

    def tokenize(self, text: str) -> list[str]:
        # Simple space-based tokenization for now. Can be expanded for n-grams.
        return text.split()
