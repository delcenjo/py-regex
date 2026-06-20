"""Service for security-sensitive regex operations (PII, Secrets, SSRF)."""

from __future__ import annotations
import re
import math
from typing import Dict, List, Any
from pyregex.infrastructure.registry import registry


class SecurityService:
    """Handles deep security analysis, secret detection, and SSRF prevention."""

    def __init__(self):
        self.registry = registry

    def scan_for_secrets(self, text: str) -> List[Dict[str, Any]]:
        """Identify potential secrets (API keys, Tokens) using entropy and patterns."""
        findings = []

        key_patterns = {
            "Generic API Key": r"[a-zA-Z0-9]{32,64}",
            "Bearer Token": r"Bearer\s+[a-zA-Z0-9\-\._~+/]+=*",
            "SSH Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
        }

        for name, pattern in key_patterns.items():
            for match in re.finditer(pattern, text):
                entropy = self.calculate_entropy(str(match.group()))
                if entropy > 3.5 or name == "SSH Private Key":
                    findings.append(
                        {
                            "type": name,
                            "value": str(match.group())[:8] + "...",
                            "start": match.start(),
                            "end": match.end(),
                            "entropy": float(round(entropy, 2)),
                            "confidence": "HIGH" if entropy > 4.5 else "MEDIUM",
                        }
                    )

        return findings

    def is_ssrf_risk(self, url: str) -> Dict[str, Any]:
        """Check if a URL points to an internal or private IP (SSRF Risk)."""
        # Private/Internal IP patterns
        private_ips = [
            r"^127\.",  # Loopback
            r"^10\.",  # Class A private
            r"^172\.(1[6-9]|2[0-9]|3[01])\.",  # Class B private
            r"^192\.168\.",  # Class C private
            r"^169\.254\.",  # Link-local (AWS Metadata etc)
            r"^localhost",  # Localhost name
            r"::1",  # IPv6 loopback
            r"fe80::",  # IPv6 link-local
        ]

        host_match = re.search(r"://([^:/]+)", url)
        if not host_match:
            return {"risk": "UNKNOWN", "reason": "Could not parse host from URL"}

        host = host_match.group(1)

        for p in private_ips:
            if re.search(p, host):
                return {
                    "risk": "HIGH",
                    "reason": f"Target matches private/internal network pattern: {p}",
                    "host": host,
                }

        return {
            "risk": "LOW",
            "reason": "URL appears to point to public infrastructure",
        }

    def calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not text:
            return 0.0

        prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
        entropy = -sum([p * math.log(p) / math.log(2.0) for p in prob])
        return entropy

    def get_pii_shield_pattern(self) -> str:
        """Return a combined pattern for all registered PII entities."""
        pii_names = self.registry.list_entities(tag="pii")
        patterns = [
            self.registry.get_pattern(name)
            for name in pii_names
            if self.registry.get_pattern(name)
        ]
        return "|".join(
            f"(?P<{name.lower()}>{p})" for name, p in zip(pii_names, patterns)
        )

    def audit_security_context(self, pattern: str) -> List[str]:
        """Check if a regex pattern itself is security-risky (eg: too loose)."""
        warnings = []
        if ".*" in pattern and not (pattern.startswith("^") and pattern.endswith("$")):
            warnings.append(
                "Loose wildcard '.*' in unanchored pattern may bypass security filters (SSRF/WAF)."
            )
        if "[^" in pattern and len(pattern) < 10:
            warnings.append("Short negative character class might be bypassable.")
        return warnings
