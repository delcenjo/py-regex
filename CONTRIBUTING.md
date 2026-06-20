# Contributing

Contributions are welcome. Please open a pull request from a feature branch.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Tests

```bash
pytest
```

## Workflow

- Branch from `main` and keep each pull request focused on a single change.
- Add or update tests for any behaviour you change.
- Make sure `pytest` passes before opening the pull request.

## Style

- Follow the existing domain-driven layout under `src/pyregex/`.
- Keep comments meaningful and concise.
