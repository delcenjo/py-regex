from __future__ import annotations
from typing import Optional
from pyregex.application.services.quick.base import QuickModule


class AliasRegistry(QuickModule):
    """Maps synonyms and keywords to internal pattern names."""

    # Internal Registry (could be loaded from JSON/YAML later)
    ALIASES = {
        "email": ["correo", "mail", "contact", "e-mail", "email"],
        "phone": ["telefono", "celular", "movil", "phone", "number", "tel"],
        "url": ["web", "link", "enlace", "url", "http", "https", "site"],
        "ip": ["direccion ip", "ip", "network", "host", "ipv4", "net", "address"],
        "id": ["dni", "nif", "documento", "id", "identification", "ssn"],
        "cc": ["credit card", "tarjeta", "visa", "mastercard"],
        "postal": ["zip code", "codigo postal", "postcode"],
        "address": ["direccion", "calle", "address", "location"],
        "name": ["nombre", "apellido", "person", "full name"],
        "username": ["usuario", "nick", "handle"],
        "password": ["clave", "contraseña", "pwd", "secret"],
        "token": ["api key", "auth", "token", "bearerr"],
        "date": ["fecha", "date", "calendar", "day"],
        "time": ["hora", "time", "clock"],
        "path": ["ruta", "archivo", "dir", "directory", "folder"],
        "uuid": ["guid", "unique id"],
        "semver": ["version", "semantic version"],
        "num": ["numero", "cantidad", "digitos", "int", "float"],
    }

    def get_pattern_by_alias(self, token: str) -> Optional[str]:
        for pattern_name, keywords in self.ALIASES.items():
            if token in keywords:
                return pattern_name
        return None
