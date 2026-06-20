from typing import List, Dict
import re


class InferenceEngine:
    """Engine to infer common regex patterns from a list of examples.

    Uses a 'Token-Alignment' approach to discover structure,
    constants, and variable character classes.
    """

    def learn(self, examples: List[str], strict: bool = True) -> Dict:
        """Infers a regex that matches all provided examples."""
        if not examples:
            return {"pattern": "", "confidence": 0.0}

        examples = [ex.strip() for ex in examples if ex.strip()]
        if not examples:
            return {"pattern": "", "confidence": 0.0}

        token_sequences = [self._tokenize(ex) for ex in examples]

        base_seq = token_sequences[0]
        for other_seq in token_sequences[1:]:
            base_seq = self._merge(base_seq, other_seq, strict)

        confidence = self._calculate_confidence(examples, base_seq)

        return {
            "pattern": self._to_regex(base_seq),
            "confidence": round(confidence, 2),
            "examples_count": len(examples),
        }

    def _calculate_confidence(
        self, examples: List[str], final_seq: List[Dict]
    ) -> float:
        """Heuristic-based confidence scoring."""
        if not examples or not final_seq:
            return 0.0

        score = 0.5

        score += min(0.3, (len(examples) / 10) * 0.1)

        is_any = any(t.get("type") == "any" for t in final_seq)
        if is_any:
            score -= 0.3

        fixed_parts = sum(1 for t in final_seq if t.get("value") is not None)
        if len(final_seq) > 0:
            score += min(0.2, (fixed_parts / len(final_seq)) * 0.2)

        return max(0.1, min(0.95, score))

    def _tokenize(self, s: str) -> List[Dict]:
        """Breaks a string into tokens of (type, value, length)."""
        if not s:
            return []

        tokens = []
        for char in s:
            ctype = self._get_type(char)
            if tokens and tokens[-1]["type"] == ctype:
                tokens[-1]["value"] += char
                tokens[-1]["length"] += 1
            else:
                tokens.append({"type": ctype, "value": char, "length": 1})
        return tokens

    def _get_type(self, char: str) -> str:
        if char.isdigit():
            return "digit"
        if char.isupper():
            return "upper"
        if char.islower():
            return "lower"
        if char.isspace():
            return "space"
        return "special"

    def _merge(self, seq1: List[Dict], seq2: List[Dict], strict: bool) -> List[Dict]:
        """Aligns two sequences and merges their characteristics."""
        if len(seq1) != len(seq2):
            # Fallback: broaden to generic match if structure varies too much
            return [{"type": "any", "value": ".*", "length": 1}]

        merged = []
        for t1, t2 in zip(seq1, seq2):
            if t1["type"] == t2["type"]:
                m_token = {
                    "type": t1["type"],
                    "value": t1["value"] if t1["value"] == t2["value"] else None,
                    "length": t1["length"]
                    if t1["length"] == t2["length"]
                    else -1,  # -1 means variable
                    "min_len": min(
                        t1.get("min_len", t1["length"]), t2.get("min_len", t2["length"])
                    ),
                    "max_len": max(
                        t1.get("max_len", t1["length"]), t2.get("max_len", t2["length"])
                    ),
                }
            else:
                m_token = {
                    "type": "mixed",
                    "value": None,
                    "length": -1,
                    "min_len": 1,
                    "max_len": 20,
                }
            merged.append(m_token)
        return merged

    def _to_regex(self, seq: List[Dict]) -> str:
        res = ["^"]
        for t in seq:
            pattern = ""
            if t["type"] == "any":
                pattern = ".*"
            elif t["value"] is not None:
                pattern = re.escape(t["value"])
            else:
                mapping = {
                    "digit": r"\d",
                    "upper": r"[A-Z]",
                    "lower": r"[a-z]",
                    "space": r"\s",
                    "special": r"[^\w\s]",
                    "mixed": r"[\w\-\.]",
                }
                char_class = mapping.get(t["type"], ".")

                if t["length"] != -1:
                    pattern = f"{char_class}{{{t['length']}}}"
                else:
                    mn = t.get("min_len", 1)
                    mx = t.get("max_len", "")
                    if mn == 1 and mx == "":
                        pattern = f"{char_class}+"
                    elif mn == mx:
                        pattern = f"{char_class}{{{mn}}}"
                    else:
                        pattern = f"{char_class}{{{mn},{mx}}}"
            res.append(pattern)
        res.append("$")
        return "".join(res)
