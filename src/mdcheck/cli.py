"""CLI orchestration per SPEC.md §3, §4."""
import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .checker import LinkChecker
from .parser import MarkdownLinkParser
from .reporter import Reporter


def _parse_allow_status(values: list[str] | None) -> list[int]:
    out: list[int] = []
    for v in values or []:
        for part in str(v).split(","):
            part = part.strip()
            if part:
                out.append(int(part))
    return out


@dataclass
class CliConfig:
    file: str | None = None
    dir: str | None = None
    recursive: bool = False
    timeout: float = 5.0
    concurrency: int = 10
    ignore_external: bool = False
    ignore_internal: bool = False
    exclude: list[str] = field(default_factory=list)
    allow_status: list[int] = field(default_factory=list)
    output: str = "text"
    verbose: int = 0

    @classmethod
    def from_args(cls, args_list: list[str]) -> "CliConfig":
        parser = build_parser()
        ns = parser.parse_args(args_list)
        return cls(
            file=ns.file,
            dir=ns.dir,
            recursive=ns.recursive,
            timeout=ns.timeout,
            concurrency=ns.concurrency,
            ignore_external=ns.ignore_external,
            ignore_internal=ns.ignore_internal,
            exclude=list(ns.exclude or []),
            allow_status=_parse_allow_status(ns.allow_status),
            output=ns.output,
            verbose=ns.verbose,
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mdcheck", description="Check Markdown links")
    p.add_argument("--file", default=None)
    p.add_argument("--dir", default=None)
    p.add_argument("-r", "--recursive", action="store_true")
    p.add_argument("--timeout", type=float, default=5.0)
    p.add_argument("--concurrency", type=int, default=10)
    p.add_argument("--ignore-external", action="store_true")
    p.add_argument("--ignore-internal", action="store_true")
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--allow-status", action="append", default=[])
    p.add_argument("--output", choices=["text", "json"], default="text")
    p.add_argument("-v", "--verbose", action="count", default=0)
    p.add_argument("--version", action="version", version="mdcheck 0.1.0")
    return p


def _gather_files(cfg: CliConfig) -> list[Path] | None:
    if cfg.file:
        return [Path(cfg.file)]
    if cfg.dir:
        root = Path(cfg.dir)
        if not root.is_dir():
            return None
        pattern = "**/*.md" if cfg.recursive else "*.md"
        return sorted(root.glob(pattern))
    return None


def main(args_list: list[str] | None = None) -> int:
    try:
        cfg = CliConfig.from_args(sys.argv[1:] if args_list is None else args_list)
    except SystemExit as e:
        return int(e.code or 2)

    if bool(cfg.file) == bool(cfg.dir):
        print("error: exactly one of --file or --dir is required", file=sys.stderr)
        return 2

    files = _gather_files(cfg)
    if files is None:
        print("error: invalid --file/--dir target", file=sys.stderr)
        return 2
    if cfg.file and not Path(cfg.file).is_file():
        print(f"error: file not found: {cfg.file}", file=sys.stderr)
        return 2

    patterns = [re.compile(p) for p in (cfg.exclude or [])]

    links = []
    for f in files:
        try:
            links.extend(MarkdownLinkParser.parse_file(f))
        except OSError as e:
            print(f"error: cannot read {f}: {e}", file=sys.stderr)
            return 2

    filtered = []
    for link in links:
        if cfg.ignore_external and link.kind == "external":
            continue
        if cfg.ignore_internal and link.kind == "internal":
            continue
        if any(p.search(link.url) for p in patterns):
            continue
        filtered.append(link)

    checker = LinkChecker(
        timeout=cfg.timeout,
        concurrency=cfg.concurrency,
        allow_status=cfg.allow_status,
    )
    results = checker.check_all(filtered)

    if cfg.output == "json":
        print(Reporter.to_json(results))
    else:
        print(Reporter.to_text(results, verbose=cfg.verbose))

    return 1 if any(not r.ok for r in results) else 0
