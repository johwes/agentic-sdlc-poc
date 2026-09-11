"""Markdown link parser per SPEC.md §2, §4."""
import re
from dataclasses import dataclass
from pathlib import Path

_INLINE_RE = re.compile(r"\[[^\]]*\]\(\s*(<[^>]+>|[^)\s]+)")
_REF_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)")
_AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
_BARE_RE = re.compile(r"\bhttps?://[^\s<>\]\)`'\"!?,;:]+")
_INLINE_CODE_RE = re.compile(r"`[^`]*`")


@dataclass
class Link:
    url: str
    file: str
    line: int
    kind: str


def _classify(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return "external"
    return "internal"


def _clean_url(raw: str) -> str:
    u = raw.strip()
    if u.startswith("<") and u.endswith(">"):
        u = u[1:-1].strip()
    return u.rstrip(".,;:!?)")


class MarkdownLinkParser:
    @staticmethod
    def parse_text(text: str, file: str = "test.md") -> list[Link]:
        links: list[Link] = []
        seen: set[str] = set()

        def add(url: str, line_no: int) -> None:
            url = _clean_url(url)
            if not url or url in seen:
                return
            seen.add(url)
            links.append(Link(url=url, file=file, line=line_no, kind=_classify(url)))

        in_fence = False
        for idx, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = _INLINE_CODE_RE.sub("", raw_line)

            for m in _INLINE_RE.finditer(line):
                add(m.group(1), idx)
            for m in _REF_DEF_RE.finditer(line):
                add(m.group(1), idx)
            for m in _AUTOLINK_RE.finditer(line):
                add(m.group(1), idx)
            for m in _BARE_RE.finditer(line):
                add(m.group(0), idx)

        return links

    @staticmethod
    def parse_file(path: str | Path) -> list[Link]:
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        return MarkdownLinkParser.parse_text(text, file=str(p))
