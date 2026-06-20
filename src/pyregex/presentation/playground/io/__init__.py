"""Playground — Sample Data & Snippets.

Provides sample test data and regex snippets for quick starts.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SampleEntry:
    """A sample regex + test data pair."""

    name: str
    category: str
    regex: str
    test_data: str
    description: str


SAMPLES: list[SampleEntry] = [
    SampleEntry(
        name="Email",
        category="personal",
        regex=r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
        test_data="Contact: user@gmail.com, admin@site.org\nBad: user@, @b.com",
        description="Detecta direcciones de email en texto",
    ),
    SampleEntry(
        name="URL",
        category="web",
        regex=r"https?://[^\s<>\"']+",
        test_data="Visit https://example.com/page?q=1 or http://docs.api.io/v2",
        description="Extrae URLs HTTP/HTTPS de texto",
    ),
    SampleEntry(
        name="IPv4",
        category="web",
        regex=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        test_data="Server: 192.168.1.1, DNS: 8.8.8.8, Bad: 999.999.999.999",
        description="Detecta direcciones IPv4",
    ),
    SampleEntry(
        name="Fecha ISO",
        category="utils",
        regex=r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])",
        test_data="Fechas: 2024-01-15, 2023-12-31\nInválidas: 2024-13-01, 2024-00-15",
        description="Valida fechas ISO 8601 (YYYY-MM-DD)",
    ),
    SampleEntry(
        name="Teléfono ES",
        category="personal",
        regex=r"(?:\+34[\s-]?)?(?:6\d{2}|7[1-9]\d|9\d{2})[\s.-]?\d{3}[\s.-]?\d{3}",
        test_data="Llama al +34 612 345 678 o al 912-345-678\nInválido: 123456",
        description="Números de teléfono españoles (móvil y fijo)",
    ),
    SampleEntry(
        name="HTML Tags",
        category="structured",
        regex=r"<([a-z][a-z0-9]*)\b[^>]*>(.*?)</\1>",
        test_data='<div class="main">Hello</div>\n<p>World</p>\n<br/>',
        description="Captura pares de tags HTML con contenido",
    ),
    SampleEntry(
        name="JSON Key-Value",
        category="structured",
        regex=r'"(\w+)"\s*:\s*"([^"]*)"',
        test_data='{"name": "PyRegex", "version": "3.0", "active": true}',
        description="Extrae pares clave-valor de strings JSON",
    ),
    SampleEntry(
        name="Log Apache",
        category="systems",
        regex=r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(\S+)\s+(\S+)\s+\S+"\s+(\d{3})\s+(\d+|-)',
        test_data='127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326',
        description="Parsea líneas de log Apache/Nginx",
    ),
    SampleEntry(
        name="Contraseña Fuerte",
        category="security",
        regex=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
        test_data="Fuerte: P@ssw0rd!\nDébil: password\nCorta: Ab1!",
        description="Valida contraseñas con mayúscula, número y carácter especial",
    ),
    SampleEntry(
        name="Docker Image",
        category="systems",
        regex=r"^(?:([a-z0-9]+(?:[._-][a-z0-9]+)*/)*)?([a-z0-9]+(?:[._-][a-z0-9]+)*)(?::([a-zA-Z0-9._-]+))?$",
        test_data="nginx:latest\nregistry.io/org/app:v1.2.3\nubuntu",
        description="Nombres de imagen Docker con registry y tag",
    ),
    SampleEntry(
        name="Semver",
        category="structured",
        regex=r"^v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+([a-zA-Z0-9.]+))?$",
        test_data="v1.2.3\n2.0.0-beta.1\n3.1.4+build.123\n1.0",
        description="Versiones semánticas con pre-release y build metadata",
    ),
    SampleEntry(
        name="SQL Injection",
        category="security",
        regex=r"(?i)(?:(?:union|select|insert|update|delete|drop|alter)[\s\w]*(?:from|into|table|set)|(?:--|#|/\*))",
        test_data="SELECT * FROM users WHERE id=1\n' OR 1=1 --\n' UNION SELECT password FROM admin --",
        description="Detecta patrones comunes de inyección SQL",
    ),
]

CHEATSHEET = """
╔══════════════════════════════════════════════════════════════╗
║                  REGEX CHEATSHEET RÁPIDA                     ║
╠══════════════════════════════════════════════════════════════╣
║ BÁSICOS        │ CUANTIFICADORES   │ CLASES                  ║
║ .  cualquier   │ *   0 o más       │ \\d  dígito [0-9]       ║
║ ^  inicio      │ +   1 o más       │ \\w  palabra [a-zA-Z_]  ║
║ $  final       │ ?   0 o 1         │ \\s  espacio            ║
║ |  alternación │ {n}  exactamente  │ \\b  word boundary      ║
║ \\  escape     │ {n,m} rango       │ [abc] conjunto          ║
║                │ *? +? lazy        │ [^ab] negación          ║
╠══════════════════════════════════════════════════════════════╣
║ GRUPOS                 │ LOOKAROUND                          ║
║ (...)   captura        │ (?=X)  lookahead positivo           ║
║ (?:...) sin captura    │ (?!X)  lookahead negativo           ║
║ (?P<n>..) con nombre   │ (?<=X) lookbehind positivo          ║
║ \\1 \\2  referencia    │ (?<!X) lookbehind negativo          ║
╠══════════════════════════════════════════════════════════════╣
║ FLAGS: (?i) case-insensitive │ (?m) multiline │ (?s) dotall  ║
╚══════════════════════════════════════════════════════════════╝
"""
