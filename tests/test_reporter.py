"""Reporter tests per SPEC.md §2.5, §4, §5 — TDD red phase.

Expected interface:
  from mdcheck.reporter import Reporter
  Reporter.to_text(results: list[Result], verbose: int = 0) -> str
  Reporter.to_json(results: list[Result]) -> str

No src/mdcheck/reporter.py exists yet — these must FAIL.
"""
import json

from mdcheck.checker import Result
from mdcheck.parser import Link
from mdcheck.reporter import Reporter


def _ok(url="https://example.com/ok"):
    return Result(
        link=Link(url=url, file="test.md", line=1, kind="external"),
        ok=True, status_or_error=200,
    )


def _bad(url="https://example.com/missing"):
    return Result(
        link=Link(url=url, file="test.md", line=2, kind="external"),
        ok=False, status_or_error=404,
    )


def test_text_summary_counts():
    text = Reporter.to_text([_ok(), _bad()])
    assert "checked" in text.lower()
    assert "passed" in text.lower() or "ok" in text.lower()
    assert "failed" in text.lower() or "fail" in text.lower()


def test_text_empty_results():
    text = Reporter.to_text([])
    assert "0" in text


def test_json_valid_schema():
    out = Reporter.to_json([_ok(), _bad()])
    data = json.loads(out)
    assert isinstance(data, (list, dict))
    raw = json.dumps(data)
    assert "https://example.com/ok" in raw
    assert "https://example.com/missing" in raw
