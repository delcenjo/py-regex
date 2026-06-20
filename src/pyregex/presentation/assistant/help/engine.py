"""Nebula — Help System."""

from __future__ import annotations
from pyregex.utils import ansi
from pyregex.presentation.assistant.ui.components import Panel

CHEATSHEET = {
    "Anclas": [
        ("^", "Inicio de línea"),
        ("$", "Fin de línea"),
        (r"\b", "Límite de palabra"),
    ],
    "Cuantificadores": [
        ("*", "0 o más"),
        ("+", "1 o más"),
        ("?", "0 o 1"),
        ("{n,m}", "Entre n y m"),
    ],
    "Clases": [
        (r"\d", "Dígito"),
        (r"\w", "Palabra"),
        (r"\s", "Espacio"),
        (".", "Cualquier char"),
    ],
    "Grupos": [
        ("()", "Grupo de captura"),
        ("(?:)", "No captura"),
        ("(?=)", "Lookahead"),
        ("(?<=)", "Lookbehind"),
    ],
    "Flags": [
        ("(?i)", "Case insensitive"),
        ("(?m)", "Multiline"),
        ("(?s)", "Dotall"),
        ("(?x)", "Verbose"),
    ],
}


def show_cheatsheet():
    """Display regex cheatsheet."""
    print(f"\n  {ansi.bold('REGEX CHEATSHEET')}")
    print(f"  {'━' * 50}")
    for category, items in CHEATSHEET.items():
        print(f"\n  {ansi.bold(category)}:")
        for syntax, desc in items:
            print(f"    {syntax:12s} {ansi.dim(desc)}")


def show_tutorials():
    """Display interactive tutorial list."""
    print(f"\n  {ansi.bold('TUTORIALES DISPONIBLES')}")
    tutorials = [
        ("1", "Introducción a Regex", "Conceptos básicos"),
        ("2", "Cuantificadores y Lazy", "Greedy vs Lazy vs Possessive"),
        ("3", "Grupos y Capturas", "Named groups, backreferences"),
        ("4", "Lookaheads y Lookbehinds", "Assertions avanzadas"),
        ("5", "Performance", "Optimización de regex"),
    ]
    for key, title, desc in tutorials:
        print(f"    [{key}] {title} — {ansi.dim(desc)}")


def show_topic(topic: str):
    """Show detailed help on a specific topic."""
    topics = {
        "email": "Usa el wizard 'email' para generar regex de email.\n  Soporta: estándar, corporativo, educativo, proveedores gratuitos.",
        "phone": "Usa el wizard 'phone' para generar regex de teléfono.\n  Soporta: local (ES/US/UK/FR/DE), internacional, con extensión.",
        "url": "Usa el wizard 'url' para generar regex de URL.\n  Soporta: HTTP/HTTPS, cualquier protocolo, relativas.",
        "ip": "Usa el wizard 'ip' para generar regex de IP.\n  Soporta: IPv4, IPv6, CIDR, validación estricta.",
    }
    if topic in topics:
        Panel(topics[topic], title=f"Ayuda: {topic}").print()
    else:
        print(f"  {ansi.dim('Tema no encontrado. Prueba: email, phone, url, ip')}")
