"""Service for mapping user intent to regex builders (Quick Mode)."""

from __future__ import annotations

from pyregex.domain.builders.base import RegexBuilder
from pyregex.domain.builders.generic import GenericBuilder
from pyregex.domain.catalog.registry import catalog_registry

class RegexService:
    """Service to handle quick mode mapping and builder coordination."""

    def __init__(self, region: str = "US"):
        self.region = region

    def map_intent(self, intent: str) -> tuple[RegexBuilder, str] | None:
        """Map a short intent string to a builder and a description.

        Examples:
            "email" -> GenericBuilder("email")
        """
        intent = intent.lower().strip()

        # English intents
        if any(w in intent for w in ["email", "mail"]):
            entry = catalog_registry.get_entry("email")
            if entry: return GenericBuilder(entry), "Standard email pattern"

        if any(w in intent for w in ["date", "calendar"]):
            fmt = "US" if self.region == "US" else "EU"
            entry = catalog_registry.get_entry("date")
            if entry:
                b = GenericBuilder(entry)
                b.config["date_format"] = fmt
                return b, f"Date pattern ({fmt})"

        if any(w in intent for w in ["number", "integer", "digit"]):
            entry = catalog_registry.get_entry("num")
            if entry:
                b = GenericBuilder(entry)
                b.config["subtype"] = "int"
                return b, "Integer number pattern"

        if any(w in intent for w in ["decimal", "float"]):
            entry = catalog_registry.get_entry("num")
            if entry:
                b = GenericBuilder(entry)
                b.config["subtype"] = "float"
                return b, "Decimal number pattern"

        if any(w in intent for w in ["phone", "tel"]):
            entry = catalog_registry.get_entry("phone")
            if entry: return GenericBuilder(entry), "Generic phone number pattern"

        if any(w in intent for w in ["dni", "nif", "identidad"]):
            entry = catalog_registry.get_entry("id")
            if entry: return GenericBuilder(entry), "Spanish ID (DNI/NIE) pattern"

        if any(w in intent for w in ["card", "credit", "tarjeta", "visa"]):
            entry = catalog_registry.get_entry("cc")
            if entry: return GenericBuilder(entry), "Credit card pattern"

        if any(w in intent for w in ["key", "api_key", "secret", "token"]):
            entry = catalog_registry.get_entry("secret")
            if entry: return GenericBuilder(entry), "Security token/API key pattern"

        # Spanish intents
        if any(w in intent for w in ["correo"]):
            entry = catalog_registry.get_entry("email")
            if entry: return GenericBuilder(entry), "Patrón de correo electrónico"

        if any(w in intent for w in ["fecha", "calendario"]):
            fmt = "EU" if self.region in ("ES", "MX", "AR") else "US"
            entry = catalog_registry.get_entry("date")
            if entry:
                b = GenericBuilder(entry)
                b.config["date_format"] = fmt
                return b, f"Patrón de fecha ({fmt})"

        if any(w in intent for w in ["numero", "entero", "digito", "número"]):
            entry = catalog_registry.get_entry("num")
            if entry:
                b = GenericBuilder(entry)
                b.config["subtype"] = "int"
                return b, "Patrón de números enteros"

        if "decimal" in intent:
            entry = catalog_registry.get_entry("num")
            if entry:
                b = GenericBuilder(entry)
                b.config["subtype"] = "float"
                return b, "Patrón de números decimales"

        if any(w in intent for w in ["telefono", "teléfono"]):
            entry = catalog_registry.get_entry("phone")
            if entry: return GenericBuilder(entry), "Patrón de número de teléfono"

        return None
