from typing import List, Set, Tuple


class TagManager:
    """Manages auto-categorization and tagging of registry patterns."""

    def __init__(self):
        # Substrings commonly found in specific pattern types
        self.auto_rules = {
            "@[a-zA-Z0-9.-]+\\.[a-zA-Z]": ["email", "contact", "network"],
            "https?://": ["url", "web", "network"],
            "\\.[0-9]{1,3}": ["ipv4", "network"],
            "[0-9]{4}-": ["finance", "date", "pii"],
            "{32}": ["hash", "security", "secret"],
        }

    def suggest_metadata(
        self, pattern_str: str, existing_tags: List[str] = None
    ) -> Tuple[List[str], str]:
        """Returns (suggested_tags, suggested_category) based on pattern inspection."""
        tags: Set[str] = set(existing_tags or [])
        category = "uncategorized"

        for rule_substring, generated_tags in self.auto_rules.items():
            if rule_substring in pattern_str:
                tags.update(generated_tags)
                # Assign first related category
                if "network" in generated_tags:
                    category = "network"
                elif "security" in generated_tags:
                    category = "security"
                elif "pii" in generated_tags:
                    category = "pii"

        return sorted(list(tags)), category
