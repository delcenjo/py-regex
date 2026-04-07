import subprocess
import sys
import os

def test_cli_help():
    """Verify that 'px --help' executes correctly."""
    result = subprocess.run(
        ["venv/bin/python3", "src/pyregex/main.py", "--help"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"}
    )
    assert result.returncode == 0
    assert "usage: px" in result.stdout.lower()

def test_cli_lang_es():
    """Verify that '--lang es' changes the output language."""
    result = subprocess.run(
        ["venv/bin/python3", "src/pyregex/main.py", "--lang", "es", "--help"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": "src"}
    )
    assert result.returncode == 0
    # In Spanish, 'usage' is often 'uso' or similar in the translated help
    assert "uso:" in result.stdout.lower() or "asistente" in result.stdout.lower()
