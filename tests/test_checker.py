"""Checker tests per SPEC.md §2, §4, §5 — TDD red phase.

Expected interface:
  from mdcheck.checker import LinkChecker, Result
  from mdcheck.parser import Link

Uses stdlib unittest.mock only (AGENTS.md Rule 2).
No src/mdcheck/checker.py exists yet — these must FAIL.
"""
from unittest import mock

import pytest
import requests

from mdcheck.checker import LinkChecker, Result
from mdcheck.parser import Link


def _ext(url="https://example.com/page"):
    return Link(url=url, file="test.md", line=1, kind="external")


def _mock_resp(status):
    r = mock.MagicMock()
    r.status_code = status
    return r


def test_external_200_ok():
    link = _ext()
    with mock.patch("requests.Session") as mock_session_cls:
        session = mock_session_cls.return_value
        session.head.return_value = _mock_resp(200)
        checker = LinkChecker()
        result = checker.check_link(link)
    assert isinstance(result, Result)
    assert result.ok is True


def test_external_404_failed():
    link = _ext("https://example.com/missing")
    with mock.patch("requests.Session") as mock_session_cls:
        session = mock_session_cls.return_value
        session.head.return_value = _mock_resp(404)
        checker = LinkChecker()
        result = checker.check_link(link)
    assert result.ok is False
    assert result.status_or_error == 404


def test_external_head_405_fallback_get_200():
    link = _ext()
    with mock.patch("requests.Session") as mock_session_cls:
        session = mock_session_cls.return_value
        session.head.return_value = _mock_resp(405)
        session.get.return_value = _mock_resp(200)
        checker = LinkChecker()
        result = checker.check_link(link)
    assert result.ok is True
    session.get.assert_called_once()


def test_external_timeout():
    link = _ext()
    with mock.patch("requests.Session") as mock_session_cls:
        session = mock_session_cls.return_value
        session.head.side_effect = requests.exceptions.Timeout
        checker = LinkChecker()
        result = checker.check_link(link)
    assert result.ok is False
    assert result.status_or_error == "Timeout"


def test_internal_exists(tmp_path):
    target = tmp_path / "target.md"
    target.write_text("# hi", encoding="utf-8")
    source = tmp_path / "doc.md"
    source.write_text("[T](target.md)", encoding="utf-8")
    link = Link(url="target.md", file=str(source), line=1, kind="internal")
    checker = LinkChecker()
    result = checker.check_link(link)
    assert result.ok is True


def test_internal_missing(tmp_path):
    source = tmp_path / "doc.md"
    source.write_text("[T](nope.md)", encoding="utf-8")
    link = Link(url="nope.md", file=str(source), line=1, kind="internal")
    checker = LinkChecker()
    result = checker.check_link(link)
    assert result.ok is False


def test_concurrency_execution():
    links = [_ext(f"https://example.com/p{i}") for i in range(5)]
    with mock.patch("requests.Session") as mock_session_cls:
        session = mock_session_cls.return_value
        session.head.return_value = _mock_resp(200)
        checker = LinkChecker(concurrency=3)
        results = checker.check_all(links)
    assert len(results) == 5
    assert all(r.ok for r in results)
