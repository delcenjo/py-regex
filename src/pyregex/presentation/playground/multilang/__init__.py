"""Playground — Multi-Language Output.

Generates regex code for Python, JavaScript, Go, Java, Rust, C#, PHP, Ruby.
"""

from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass
class LanguageOutput:
    """Regex code in a specific language."""

    language: str
    code: str
    import_line: str = ""
    note: str = ""


class MultiLangExporter:
    """
    Exports regex patterns in multiple programming languages.

    Adapts syntax, flags, and API calls for each target language.
    """

    def export(
        self, pattern: str, flags: int = 0, lang: str = "python"
    ) -> LanguageOutput:
        """Export regex for a specific language."""
        exporters = {
            "python": self._python,
            "javascript": self._javascript,
            "go": self._go,
            "java": self._java,
            "rust": self._rust,
            "csharp": self._csharp,
            "php": self._php,
            "ruby": self._ruby,
        }
        fn = exporters.get(lang, self._python)
        return fn(pattern, flags)

    def export_all(self, pattern: str, flags: int = 0) -> list[LanguageOutput]:
        """Export regex in all supported languages."""
        langs = ["python", "javascript", "go", "java", "rust", "csharp", "php", "ruby"]
        return [self.export(pattern, flags, lang) for lang in langs]

    def _python(self, pattern: str, flags: int) -> LanguageOutput:
        flag_str = self._python_flags(flags)
        if flag_str:
            code = f'import re\n\npattern = re.compile(r"{pattern}", {flag_str})'
        else:
            code = f'import re\n\npattern = re.compile(r"{pattern}")'
        code += "\nmatches = pattern.findall(text)\nfor m in pattern.finditer(text):\n    print(m.group())"
        return LanguageOutput(language="python", code=code, import_line="import re")

    def _javascript(self, pattern: str, flags: int) -> LanguageOutput:
        js_flags = self._js_flags(flags)
        code = f"const pattern = /{pattern}/{js_flags};\n"
        code += "const matches = text.matchAll(pattern);\n"
        code += "for (const m of matches) {\n  console.log(m[0]);\n}"
        return LanguageOutput(
            language="javascript",
            code=code,
            note="Lookbehind no soportado en todos los navegadores",
        )

    def _go(self, pattern: str, flags: int) -> LanguageOutput:
        go_pattern = pattern
        if flags & re.IGNORECASE:
            go_pattern = f"(?i){go_pattern}"
        if flags & re.MULTILINE:
            go_pattern = f"(?m){go_pattern}"
        if flags & re.DOTALL:
            go_pattern = f"(?s){go_pattern}"

        code = 'import "regexp"\n\n'
        code += f"pattern := regexp.MustCompile(`{go_pattern}`)\n"
        code += "matches := pattern.FindAllString(text, -1)\n"
        code += "for _, m := range matches {\n    fmt.Println(m)\n}"
        return LanguageOutput(
            language="go",
            code=code,
            import_line='"regexp"',
            note="Go usa RE2: no soporta lookahead/lookbehind",
        )

    def _java(self, pattern: str, flags: int) -> LanguageOutput:
        java_pattern = pattern.replace("\\", "\\\\").replace('"', '\\"')
        flag_parts = []
        if flags & re.IGNORECASE:
            flag_parts.append("Pattern.CASE_INSENSITIVE")
        if flags & re.MULTILINE:
            flag_parts.append("Pattern.MULTILINE")
        if flags & re.DOTALL:
            flag_parts.append("Pattern.DOTALL")

        flag_str = " | ".join(flag_parts) if flag_parts else "0"
        code = "import java.util.regex.*;\n\n"
        code += f'Pattern pattern = Pattern.compile("{java_pattern}", {flag_str});\n'
        code += "Matcher matcher = pattern.matcher(text);\n"
        code += "while (matcher.find()) {\n    System.out.println(matcher.group());\n}"
        return LanguageOutput(
            language="java", code=code, import_line="import java.util.regex.*;"
        )

    def _rust(self, pattern: str, flags: int) -> LanguageOutput:
        rust_pattern = pattern
        if flags & re.IGNORECASE:
            rust_pattern = f"(?i){rust_pattern}"
        if flags & re.MULTILINE:
            rust_pattern = f"(?m){rust_pattern}"
        if flags & re.DOTALL:
            rust_pattern = f"(?s){rust_pattern}"

        code = "use regex::Regex;\n\n"
        code += f'let pattern = Regex::new(r"{rust_pattern}").unwrap();\n'
        code += (
            'for m in pattern.find_iter(text) {\n    println!("{{}}", m.as_str());\n}'
        )
        return LanguageOutput(
            language="rust",
            code=code,
            import_line="use regex::Regex;",
            note='Cargo.toml: regex = "1"',
        )

    def _csharp(self, pattern: str, flags: int) -> LanguageOutput:
        opts = []
        if flags & re.IGNORECASE:
            opts.append("RegexOptions.IgnoreCase")
        if flags & re.MULTILINE:
            opts.append("RegexOptions.Multiline")
        if flags & re.DOTALL:
            opts.append("RegexOptions.Singleline")

        opts_str = " | ".join(opts) if opts else "RegexOptions.None"
        cs_pattern = pattern.replace('"', '\\"')
        code = "using System.Text.RegularExpressions;\n\n"
        code += f'var pattern = new Regex(@"{cs_pattern}", {opts_str});\n'
        code += "foreach (Match m in pattern.Matches(text))\n{\n    Console.WriteLine(m.Value);\n}"
        return LanguageOutput(
            language="csharp",
            code=code,
            import_line="using System.Text.RegularExpressions;",
        )

    def _php(self, pattern: str, flags: int) -> LanguageOutput:
        php_flags = ""
        if flags & re.IGNORECASE:
            php_flags += "i"
        if flags & re.MULTILINE:
            php_flags += "m"
        if flags & re.DOTALL:
            php_flags += "s"
        if flags & re.VERBOSE:
            php_flags += "x"
        if flags & re.UNICODE:
            php_flags += "u"

        code = f"<?php\n$pattern = '/{pattern}/{php_flags}';\n"
        code += "preg_match_all($pattern, $text, $matches);\n"
        code += "foreach ($matches[0] as $m) {\n    echo $m . PHP_EOL;\n}"
        return LanguageOutput(language="php", code=code)

    def _ruby(self, pattern: str, flags: int) -> LanguageOutput:
        ruby_flags = ""
        if flags & re.IGNORECASE:
            ruby_flags += "i"
        if flags & re.MULTILINE:
            ruby_flags += "m"
        if flags & re.VERBOSE:
            ruby_flags += "x"

        code = f"pattern = /{pattern}/{ruby_flags}\n"
        code += "text.scan(pattern) { |m| puts m }"
        return LanguageOutput(language="ruby", code=code)

    @staticmethod
    def _python_flags(flags: int) -> str:
        parts = []
        mapping = {
            re.IGNORECASE: "re.IGNORECASE",
            re.MULTILINE: "re.MULTILINE",
            re.DOTALL: "re.DOTALL",
            re.VERBOSE: "re.VERBOSE",
            re.ASCII: "re.ASCII",
            re.UNICODE: "re.UNICODE",
        }
        for flag, name in mapping.items():
            if flags & flag:
                parts.append(name)
        return " | ".join(parts)

    @staticmethod
    def _js_flags(flags: int) -> str:
        f = "g"
        if flags & re.IGNORECASE:
            f += "i"
        if flags & re.MULTILINE:
            f += "m"
        if flags & re.DOTALL:
            f += "s"
        if flags & re.UNICODE:
            f += "u"
        return f
