import re
import unicodedata
from pyregex.application.services.quick.base import QuickModule


class Normalizer(QuickModule):
    """Normalizes input text for better tokenization and matching."""

    def normalize(self, text: str) -> str:
        text = text.lower()
        text = "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text


class Tokenizer(QuickModule):
    """Splits normalized text into searchable tokens."""

    def tokenize(self, text: str) -> list[str]:
        return text.split()
