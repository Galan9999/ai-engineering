from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    "app/__init__.py",
    "app/main.py",
    "app/config.py",
    "app/routers/__init__.py",
    "app/routers/estimations.py",
    "app/services/__init__.py",
    "app/services/llm_service.py",
    "app/context/__init__.py",
    "app/context/examples.py",
    ".env.example",
    ".gitignore",
    "pyproject.toml",
    "README.md",
]


@pytest.mark.parametrize("path", REQUIRED)
def test_required_file_exists(path):
    assert (ROOT / path).is_file(), f"Falta {path}"


def test_env_is_ignored():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()
