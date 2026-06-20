"""Nebula Shell — ASCII Banner & Splash Screen."""

from __future__ import annotations
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n


BANNER_ART = r"""
  ╔══════════════════════════════════════════════════════════════════╗
  ║                                                                  ║
  ║      ███╗   ██╗███████╗██████╗ ██╗   ██╗██╗      █████╗          ║
  ║      ████╗  ██║██╔════╝██╔══██╗██║   ██║██║     ██╔══██╗         ║
  ║      ██╔██╗ ██║█████╗  ██████╔╝██║   ██║██║     ███████║         ║
  ║      ██║╚██╗██║██╔══╝  ██╔══██╗██║   ██║██║     ██╔══██║         ║
  ║      ██║ ╚████║███████╗██████╔╝╚██████╔╝███████╗██║  ██║         ║
  ║      ╚═╝  ╚═══╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝         ║
  ║                                                                  ║
  ╟──────────────────────────────────────────────────────────────────╢
  ║              PyRegex Interactive Assistant Engine                ║
  ║                 [ ARCHITECTURE • AI • REGEX ]                    ║
  ║                         v2.0 — Nebula                            ║
  ╚══════════════════════════════════════════════════════════════════╝
"""


TIPS = [
    lambda: i18n.t("assistant.banner.help_tip", fallback="Tip: Escribe 'help' para lista completa de comandos"),
    lambda: i18n.t("assistant.banner.shortcuts_tip", fallback="Tip: Usa 'email', 'phone', 'url' para atajos directos a wizards"),
    lambda: i18n.t("assistant.banner.back_tip", fallback="Tip: Escribe 'back' o 'b' para volver atrás en cualquier momento"),
    lambda: i18n.t("assistant.banner.wizard_back_tip", fallback="Tip: Los wizards soportan 'b' para ir al paso anterior"),
    lambda: i18n.t("assistant.banner.status_tip", fallback="Tip: Escribe 'status' para ver estadísticas de la sesión"),
    lambda: i18n.t("assistant.banner.merge_tip", fallback="Tip: Puedes combinar regex con el wizard 'merge'"),
    lambda: i18n.t("assistant.banner.history_tip", fallback="Tip: Usa 'history' para ver tu historial de comandos"),
    lambda: i18n.t("assistant.banner.save_tip", fallback="Tip: Los patrones generados se pueden guardar, editar y explicar"),
]


def show_banner(module_count: int = 0, wizard_count: int = 0) -> None:
    """Display the splash screen."""
    primary = "#00d4ff"
    
    print(ansi.fg_hex(primary, ansi.bold(BANNER_ART)))

    modules_label = i18n.t("assistant.banner.modules", fallback="Modules Loaded")
    wizards_label = i18n.t("assistant.banner.wizards", fallback="Expressions")
    
    print(
        f"    {ansi.dim('::')} {ansi.bold(str(module_count))} {ansi.dim(modules_label)}  "
        f"  {ansi.dim('::')} {ansi.bold(str(wizard_count))} {ansi.dim(wizards_label)}"
    )
    
    type_hint = i18n.t("assistant.banner.type", fallback="Technical Command:")
    print(f"    {ansi.dim(type_hint)} {ansi.fg_hex(primary, 'help')} {ansi.dim('to list architectural primitives')}")

    import random
    tip = random.choice(TIPS)()
    print(f"\n    {ansi.fg_hex(primary, '∫')} {ansi.dim(tip)}")
    print()


def show_goodbye() -> None:
    """Display goodbye message."""
    goodbye_msg = i18n.t("assistant.banner.goodbye", fallback="[EXIT] Assistant context saved correctly.")
    print(f"\n    {ansi.dim(goodbye_msg)}\n")
