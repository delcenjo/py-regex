import hashlib
import random


def redact(value: str, salt: str, ptype: str) -> str:
    return "*" * len(value)


def hash_consistently(value: str, salt: str, ptype: str) -> str:
    return hashlib.sha256((value + salt).encode()).hexdigest()[:16]


def replace_with_placeholder(value: str, salt: str, ptype: str) -> str:
    return f"<{ptype.upper()}>"


def fake_data(value: str, salt: str, ptype: str) -> str:
    """Generates deterministic fake data of the same type without heavy dependencies."""
    seed = int(hashlib.md5(value.encode()).hexdigest(), 16)
    rng = random.Random(seed)

    ptype = ptype.upper()
    if ptype == "EMAIL":
        names = ["user", "admin", "test", "demo", "info", "contact", "system"]
        domains = ["example.com", "test.org", "demo.net", "dummy.io"]
        n = rng.choice(names)
        num = rng.randint(1, 999)
        d = rng.choice(domains)
        return f"{n}{num}@{d}"
    elif ptype == "PHONE":
        return f"+34 {rng.randint(600, 799)} {rng.randint(100, 999)} {rng.randint(100, 999)}"
    elif ptype == "DNI":
        nums = str(rng.randint(10000000, 99999999))
        letters = "TRWQAGMYLPFDSBCHNJZ"
        idx = int(nums) % 23
        return f"{nums}{letters[idx]}"
    elif ptype == "CREDIT_CARD":
        prefix = rng.choice(["4", "51", "52", "53", "54", "55"])
        rem = 16 - len(prefix)
        return prefix + "".join(str(rng.randint(0, 9)) for _ in range(rem))
    elif ptype == "API_KEY":
        return "sk-fake-" + "".join(
            rng.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=24)
        )
    elif ptype == "AWS_SECRET":
        return "AKIA" + "".join(
            rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=16)
        )
    elif ptype == "JWT":
        return "eyJhbGciOiJIUzI1NiIsIn.eyJmYWtlIjoidHJ1ZSJ.a1b2c3d4e5f6g7h8i9j0"
    elif ptype == "PASSWORD":
        return "fake_p4ssw0rd!"

    return f"fake_{ptype.lower()}_{rng.randint(1000, 9999)}"


MODES = {
    "redact": redact,
    "hash": hash_consistently,
    "replace": replace_with_placeholder,
    "fake": fake_data,
}
