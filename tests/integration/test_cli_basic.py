import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAIN = os.path.join(ROOT, "src", "pyregex", "main.py")
ENV = {**os.environ, "PYTHONPATH": os.path.join(ROOT, "src")}


def test_cli_help():
    """Verify that 'px --help' executes correctly."""
    result = subprocess.run([sys.executable, MAIN, "--help"], capture_output=True, text=True, env=ENV)
    assert result.returncode == 0
    assert "usage: px" in result.stdout.lower()


def test_cli_lang_es():
    """Verify that '--lang es' changes the output language."""
    result = subprocess.run(
        [sys.executable, MAIN, "--lang", "es", "--help"], capture_output=True, text=True, env=ENV
    )
    assert result.returncode == 0
    assert "uso:" in result.stdout.lower() or "asistente" in result.stdout.lower()
