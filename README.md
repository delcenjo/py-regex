# PyRegex

![CI](https://github.com/delcenjo/py-regex/actions/workflows/ci.yml/badge.svg)

A command-line toolkit for working with regular expressions: explain and
visualise them, test them, profile their performance (including catastrophic
backtracking / ReDoS), and apply them to files (PII auditing and masking). It
also ships with an interactive shell and a small, extensible YAML catalog of
common patterns.

Installs the `pyregex` command (alias `px`).

## Install

```bash
git clone https://github.com/delcenjo/py-regex.git
cd py-regex
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Commands

| Command | Description |
| ------- | ----------- |
| `explain` | Parse a regex into an AST and describe it in plain language; export to Mermaid |
| `play` | Interactive terminal playground — edit a pattern and test data live |
| `test` | Run regex unit-test suites defined in YAML |
| `bench` | Profile a pattern and detect catastrophic backtracking (ReDoS) |
| `audit` | Scan files for PII (emails, phone numbers, card numbers) |
| `mask` | Anonymise PII in text (hashing or fake replacement) |
| `validate` / `extract` / `replace` / `transform` | Apply a pattern to text or files |
| `generate` / `learn` | Synthesise sample text from a pattern / infer a pattern from examples |
| `save` / `list` / `delete` | Manage a local registry of saved patterns |
| `assistant` | Interactive shell to browse the catalog and build patterns step by step |
| `config` / `history` / `export` | Settings, command history and output export |

Run `px <command> --help` for the options of each.

## Examples

```bash
px explain "^[a-z]+$"            # describe a pattern in plain language
px bench "(a+)+$"               # flag catastrophic backtracking
px audit access.log             # find PII in a file
px mask --type email notes.txt  # mask email addresses
```

## Catalog

Reusable patterns live under `catalog/<category>/<name>/wizard.yaml` (email, url,
ipv4, ipv6, uuid, credit_card, iban, iso_date, …). Add your own by dropping a new
`wizard.yaml` into a folder — the registry discovers it automatically. The
catalog is optional; every command works without it.

## Architecture

The code follows a domain-driven layout:

```
src/pyregex/
  domain/          regex parsing, AST, ReDoS analysis, catalog registry
  application/     services (audit, mask, validate, …)
  infrastructure/  persistence and saved-pattern registry
  presentation/    CLI commands and the interactive shell
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
