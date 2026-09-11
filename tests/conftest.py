"""Shared pytest fixtures per SPEC.md §5.

Uses stdlib unittest.mock only (no requests-mock / responses / pytest-mock)
per AGENTS.md Rule 2.
"""
import sys
from pathlib import Path
from unittest import mock

import pytest

# Make `src/` importable so `import mdcheck.*` works without install.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def sample_md() -> str:
    return """# Sample

Inline: [Example](https://example.com/page).

Reference: [Docs][docs-ref].

[docs-ref]: https://docs.example.com/guide

Autolink: <https://autolink.example.com>.

Bare: https://bare.example.com/path
"""


@pytest.fixture
def mock_session():
    """Generic mocked requests.Session for future checker tests."""
    session = mock.MagicMock()
    response = mock.MagicMock()
    response.status_code = 200
    session.head.return_value = response
    session.get.return_value = response
    return session
