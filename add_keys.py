import json

def update_file(path, new_keys):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "playground" not in data:
        data["playground"] = {}
    data["playground"].update(new_keys["playground"])
    
    if "assistant" not in data:
        data["assistant"] = {}
        data["assistant"]["banner"] = {}
        data["assistant"]["repl"] = {}
    if "banner" not in data["assistant"]:
        data["assistant"]["banner"] = {}
    data["assistant"]["banner"].update(new_keys["assistant"]["banner"])
    if "repl" not in data["assistant"]:
        data["assistant"]["repl"] = {}
    data["assistant"]["repl"].update(new_keys["assistant"]["repl"])
    
    if "common" not in data:
        data["common"] = {}
    data["common"].update(new_keys["common"])
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

en_keys = {
    "playground": {
        "empty_regex": "Escribe un regex arriba...",  # Wait, English needs to be translated!
        "no_matches": "Sin coincidencias",
        "matches_count": "{count} coincidencia(s)",
        "no_groups": "Sin grupos de captura",
        "use_parens": "Usa (...) para crear grupos",
        "explain_prompt": "Escribe un regex para ver la explicación",
        "explain_header": "EXPLICACIÓN:",
        "debug_prompt": "Necesitas regex + texto para debug",
        "replace_header": "SUSTITUCIÓN:",
        "replace_pattern": "Patrón de reemplazo: {pattern}",
        "replace_empty": "(vacío)",
        "replace_count": "Sustituciones: {count}",
        "export_prompt": "Escribe un regex para exportar",
        "optimize_prompt": "Escribe un regex para optimizar",
        "warnings": "ADVERTENCIAS:",
        "suggestions": "SUGERENCIAS:",
        "footer_hints": "Tab entre paneles | F1-F7 para vistas"
    },
    "assistant": {
        "banner": {
            "help_tip": "Tip: Escribe 'help' para lista completa de comandos",
            "back_tip": "Tip: Escribe 'back' o 'b' para volver atrás en cualquier momento",
            "status_tip": "Tip: Escribe 'status' para ver estadísticas de la sesión",
            "start_tip": "Escribe help para comenzar o un comando directo"
        },
        "repl": {
            "back_desc": "Volver atrás"
        }
    },
    "common": {
        "back": "Volver",
        "file_not_found": "Archivo no encontrado: {file}",
        "parse_error": "Error de análisis sintáctico: {error}"
    }
}

es_keys = dict(en_keys) # Copies the spanish text
es_keys["playground"]["empty_regex"] = "Escribe un regex arriba..."
es_keys["playground"]["no_matches"] = "Sin coincidencias"
es_keys["playground"]["matches_count"] = "{count} coincidencia(s)"
en_keys["playground"]["empty_regex"] = "Type a regex above..."
en_keys["playground"]["no_matches"] = "No matches"
en_keys["playground"]["matches_count"] = "{count} match(es)"
en_keys["playground"]["no_groups"] = "No capture groups"
en_keys["playground"]["use_parens"] = "Use (...) to create groups"
en_keys["playground"]["explain_prompt"] = "Type a regex to see explanation"
en_keys["playground"]["explain_header"] = "EXPLANATION:"
en_keys["playground"]["debug_prompt"] = "Regex + text required for debug"
en_keys["playground"]["replace_header"] = "REPLACEMENT:"
en_keys["playground"]["replace_pattern"] = "Replacement pattern: {pattern}"
en_keys["playground"]["replace_empty"] = "(empty)"
en_keys["playground"]["replace_count"] = "Substitutions: {count}"
en_keys["playground"]["export_prompt"] = "Type a regex to export"
en_keys["playground"]["optimize_prompt"] = "Type a regex to optimize"
en_keys["playground"]["warnings"] = "WARNINGS:"
en_keys["playground"]["suggestions"] = "SUGGESTIONS:"
en_keys["playground"]["footer_hints"] = "Tab switches panels | F1-F7 for views"

en_keys["assistant"]["banner"]["help_tip"] = "Tip: Type 'help' for full command list"
en_keys["assistant"]["banner"]["back_tip"] = "Tip: Type 'back' or 'b' to go back at any time"
en_keys["assistant"]["banner"]["status_tip"] = "Tip: Type 'status' to see session stats"
en_keys["assistant"]["banner"]["start_tip"] = "Type help to start or a direct command"
en_keys["assistant"]["repl"]["back_desc"] = "Go back"

en_keys["common"]["back"] = "Back"
en_keys["common"]["file_not_found"] = "File not found: {file}"
en_keys["common"]["parse_error"] = "Syntax parsing error: {error}"


update_file('src/pyregex/locales/en/messages.json', en_keys)
update_file('src/pyregex/locales/es/messages.json', es_keys)
