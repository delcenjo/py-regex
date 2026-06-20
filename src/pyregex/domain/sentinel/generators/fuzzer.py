"""Sentinel Engine — Synthetic Data Fuzzer.

Wraps the 'Faker' library to dynamically generate hundreds of random
inputs for regex stress testing.
"""

from __future__ import annotations
import random
from typing import List

try:
    from faker import Faker

    _FAKER_AVAILABLE = True
except ImportError:
    _FAKER_AVAILABLE = False


class Fuzzer:
    """Generates synthetic data for regex falsification testing."""

    def __init__(self, seed: int | None = None):
        if not _FAKER_AVAILABLE:
            raise RuntimeError(
                "Faker is required for the Sentinel Fuzzer. Run: pip install faker"
            )

        self.fake = Faker(["es_ES", "en_US"])
        if seed is not None:
            Faker.seed(seed)

    def generate(self, fuzzer_type: str, count: int = 10) -> List[str]:
        """Generate *count* random strings of *fuzzer_type*."""
        if not hasattr(self, f"_gen_{fuzzer_type}"):
            # Fallback to random alphanumeric words
            return [self.fake.word() for _ in range(count)]

        method = getattr(self, f"_gen_{fuzzer_type}")
        return [method() for _ in range(count)]

    def _gen_email(self) -> str:
        return self.fake.email()

    def _gen_ipv4(self) -> str:
        return self.fake.ipv4()

    def _gen_ipv6(self) -> str:
        return self.fake.ipv6()

    def _gen_url(self) -> str:
        return self.fake.url()

    def _gen_mac_address(self) -> str:
        return self.fake.mac_address()

    def _gen_uuid4(self) -> str:
        return self.fake.uuid4()

    def _gen_credit_card(self) -> str:
        return self.fake.credit_card_number()

    def _gen_date(self) -> str:
        return self.fake.date()

    def _gen_time(self) -> str:
        return self.fake.time()

    def _gen_word(self) -> str:
        return self.fake.word()

    def _gen_text(self) -> str:
        return self.fake.text(max_nb_chars=100)

    def _gen_name(self) -> str:
        return self.fake.name()

    def _gen_company(self) -> str:
        return self.fake.company()

    def _gen_address(self) -> str:
        # Faker returns newlines in addresses, remove them for simple testing
        return self.fake.address().replace("\n", ", ")

    def _gen_phone(self) -> str:
        return self.fake.phone_number()

    def _gen_iban(self) -> str:
        return self.fake.iban()

    def _gen_isbn(self) -> str:
        return self.fake.isbn13()

    def _gen_hex_color(self) -> str:
        return self.fake.hex_color()

    def _gen_ssn(self) -> str:
        return self.fake.ssn()

    def _gen_garbage(self) -> str:
        """Injects heavily randomized punctuation and special chars to break regexes."""
        charset = (
            "!@#$%^&*()_+{}|:<>?-=[]\\;',./\" \t\n\r"
            + "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        )
        length = random.randint(5, 50)
        return "".join(random.choice(charset) for _ in range(length))
