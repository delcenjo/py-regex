PRESETS = {
    "pii": {
        "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "PHONE": r"\+?34[\s\-\.]?[6-9](?:[\s\-\.]?\d){8}\b",
        "DNI": r"\b[0-9XYZ]\d{7}[TRWQAGMYLPFDSBCHNJZ]{1}\b",
        "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b",
        "IBAN": r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b",
        "NIF": r"\b[0-9XYZ]\d{7}[TRWQAGMYLPFDSBCHNJZ]\b",
    },
    "secrets": {
        "API_KEY": r"(sk|ak)-[a-zA-Z0-9]{32,}",
        "AWS_SECRET": r"(AKIA|ASIA)[A-Z0-9]{16}",
        "JWT": r"eyJ[A-Za-z0-9-_]+?\.eyJ[A-Za-z0-9-_]+?\.[A-Za-z0-9-_]+",
        "PASSWORD": r"(password|pwd)[:\s]*['\"]?[^'\s]{8,}['\"]?",
    },
    "llm_safety": {
        "PROMPT_INJECTION": r"(?i)(?:ignore previous|disregard|forget|new instruction|overwrite|system prompt|you are now|act as)",
        "JAILBREAK": r"(?i)(?:dan mode|jailbreak|unfiltered|bypassing|exploit|respond as)",
        "OUTPUT_FORMAT_HIJACK": r"(?i)(?:only output json|no text|raw code|don't include explanations)",
    },
    "web": {
        "IP": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        "URL": r"https?://[^\s$.?#].[^\s]*",
        "DOMAIN": r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b",
    },
    "systems": {
        "PATH": r"(?:/[a-zA-Z0-9\._\-]+)+",
        "UUID": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
    },
}
