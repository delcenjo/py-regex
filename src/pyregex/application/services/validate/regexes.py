import re

VALIDATORS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone_es": r"^\+?34[\s\-\.]?[6-9](?:[\s\-\.]?\d){8}$",
    "dni": r"^[0-9XYZ]\d{7}[TRWQAGMYLPFDSBCHNJZ]$",
    "credit_card": {
        "pattern": r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})$",
        "luhn_check": True,
    },
    "url": r"^https?://[^\s$.?#].[^\s]*$",
    "ipv4": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
    "uuid": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
    "mac": r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$",
    "semver": r"^\d+\.\d+\.\d+(?:-[\w.]+)?(?:\+[\w.]+)?$",
    "iso_date": r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$",
    "iban": {"pattern": r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", "iban_check": True},
    "nif": {"pattern": r"^[0-9XYZ]\d{7}[TRWQAGMYLPFDSBCHNJZ]$", "nif_check": True},
}


def luhn_check(number_str: str) -> bool:
    """Validates a credit card number using the Luhn algorithm."""
    digits = [int(d) for d in number_str if d.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    # Use standard loop instead of slicing to satisfy strict linters
    n = len(digits)
    for i in range(n):
        d = digits[n - 1 - i]
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def iban_check(iban: str) -> bool:
    """Validates an IBAN using the ISO 7064 mod-97-10 algorithm."""
    iban = iban.replace(" ", "").upper()
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$", iban):
        return False
    # Move first 4 characters to the end
    rearranged = iban[4:] + iban[:4]
    # Replace letters with digits: A=10, B=11, ..., Z=35
    numeric_iban = ""
    for char in rearranged:
        if char.isdigit():
            numeric_iban += char
        else:
            numeric_iban += str(ord(char) - ord("A") + 10)
    return int(numeric_iban) % 97 == 1


def nif_check(nif: str) -> bool:
    """Validates a Spanish NIF (DNI/NIE) using the lookup table."""
    nif = nif.upper().replace("-", "").replace(" ", "")
    if not re.match(r"^[0-9XYZ]\d{7}[TRWQAGMYLPFDSBCHNJZ]$", nif):
        return False
    table = "TRWQAGMYLPFDSBCHNJZ"
    first = nif[0]
    if first == "X":
        val = "0" + nif[1:]
    elif first == "Y":
        val = "1" + nif[1:]
    elif first == "Z":
        val = "2" + nif[1:]
    else:
        val = nif
    number = int(val[:8])
    return table[number % 23] == nif[-1]
