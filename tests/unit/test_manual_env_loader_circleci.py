import os
from pathlib import Path
from types import ModuleType
from typing import Any

import importlib
import sys

import pytest


pytestmark = pytest.mark.circleci


def test_manual_env_loader_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Create a temporary package layout to import the module cleanly
    pkg_dir = tmp_path / "gmail_client_impl"
    src_dir = pkg_dir
    src_dir.mkdir(parents=True)

    # Write a minimal __init__ and copy of the target file contents
    (src_dir / "__init__.py").write_text("\n")

    # Read original file content
    from pathlib import Path as P
    original = (P.cwd() / "src" / "gmail_client_impl" / "src" / "gmail_client_impl" / "gmail_impl.py").read_text()
    # Force the fallback path by making the dotenv import raise ImportError inside the copied file
    original = original.replace(
        "from dotenv import load_dotenv",
        "raise ImportError()  # forced fallback",
    )

    # Save as gmail_impl.py within temp package path so import triggers its top-level loader
    (src_dir / "gmail_impl.py").write_text(original)

    # Create a .env in current working directory of import to be picked up by manual loader
    (tmp_path / ".env").write_text("TEST_ENV_LOADER_KEY=loaded_value\n")

    # Ensure python can import from our temp directory and chdir there
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))

    # Do not forcefully block python-dotenv; allow either dotenv or fallback to load .env

    # Ensure prior cached modules don't short-circuit our temp import
    for name in ["gmail_client_impl.gmail_impl", "gmail_client_impl"]:
        if name in sys.modules:
            del sys.modules[name]

    # Import the temp module which will execute top-level fallback loader
    mod: ModuleType = importlib.import_module("gmail_client_impl.gmail_impl")

    # Verify the env var from .env was loaded into process env
    assert os.environ.get("TEST_ENV_LOADER_KEY") == "loaded_value"

    # Sanity: module exposes GmailClient
    assert hasattr(mod, "GmailClient")


