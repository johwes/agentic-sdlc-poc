"""Parser unit tests per SPEC.md §5 — TDD First (Rule 1).

Expected interface (SPEC.md §4):
  from mdcheck.parser import MarkdownLinkParser, Link
  Link{url, file, line, kind} where kind in {"external", "internal"}
  MarkdownLinkParser.parse_text(text, file="test.md") -> list[Link]
  MarkdownLinkParser.parse_file(path) -> list[Link]

No network. No src/ implementation exists yet — these must FAIL (red).
"""
import pytest

from mdcheck.parser import Link, MarkdownLinkParser


def test_inline_link():
    text = "[Example](https://example.com/page)"
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    assert len(links) == 1
    assert links[0].url == "https://example.com/page"
    assert links[0].kind == "external"


def test_reference_link():
    text = "[Docs][docs-ref]\n\n[docs-ref]: https://docs.example.com/guide\n"
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    urls = [li.url for li in links]
    assert "https://docs.example.com/guide" in urls


def test_autolink():
    text = "See <https://autolink.example.com> for details."
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    assert "https://autolink.example.com" in [li.url for li in links]


def test_bare_url():
    text = "Visit https://bare.example.com/path today."
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    assert "https://bare.example.com/path" in [li.url for li in links]


def test_ignores_fenced_code_block():
    text = (
        "Real: [Ok](https://ok.example.com)\n"
        "```\n"
        "[Fake](https://fake.example.com)\n"
        "https://fake2.example.com\n"
        "```\n"
    )
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    urls = [li.url for li in links]
    assert "https://ok.example.com" in urls
    assert "https://fake.example.com" not in urls
    assert "https://fake2.example.com" not in urls


def test_ignores_inline_code():
    text = "Real [Ok](https://ok.example.com) but `[Fake](https://fake.example.com)`."
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    urls = [li.url for li in links]
    assert "https://ok.example.com" in urls
    assert "https://fake.example.com" not in urls


def test_line_numbers(tmp_path=None):
    text = "First [A](https://a.example.com)\nSecond [B](https://b.example.com)\n"
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    by_url = {li.url: li.line for li in links}
    assert by_url["https://a.example.com"] == 1
    assert by_url["https://b.example.com"] == 2


def test_dedup_unique_links():
    text = "[A](https://dup.example.com) and [A again](https://dup.example.com)"
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    urls = [li.url for li in links]
    assert urls.count("https://dup.example.com") == 1


def test_internal_vs_external_classification():
    text = "[Local](./docs/guide.md) and [Remote](https://example.com)"
    links = MarkdownLinkParser.parse_text(text, file="test.md")
    by_url = {li.url: li.kind for li in links}
    assert by_url["./docs/guide.md"] == "internal"
    assert by_url["https://example.com"] == "external"


def test_parse_file(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("[Hi](https://example.com/hi)\n", encoding="utf-8")
    links = MarkdownLinkParser.parse_file(str(md))
    assert len(links) == 1
    assert links[0].url == "https://example.com/hi"
    assert links[0].file == str(md)
    assert links[0].line == 1


def test_sample_md_fixture(sample_md):
    links = MarkdownLinkParser.parse_text(sample_md, file="sample.md")
    urls = {li.url for li in links}
    assert "https://example.com/page" in urls
    assert "https://docs.example.com/guide" in urls
