# SPEC.md — Markdown Link Checker CLI (Python)

## 1. Overview
Minimalist CLI tool to validate links in local Markdown files. Detects broken external URLs and invalid internal relative paths.

**Goals:**
* Parse one file or directory of `.md` files
* Extract inline `[text](url)`, reference `[text][ref]`, bare URLs, relative paths
* Check HTTP(S) status concurrently + verify local files exist
* Exit non-zero on broken links for CI use

**Non-Goals:**
* No HTML rendering, no crawling, no auto-fix, no GUI, no caching v1

## 2. Core Features
1. **Parser:** Extract unique links with source `file:line`. Support inline, reference-style, autolinks `<http...>`, bare `http(s)://`. Ignore code blocks / inline code.
2. **Classifier:** `external` (http/https) vs `internal` (`./`, `../`, `/`, `*.md#anchor`, `#anchor`).
3. **Checker:**
   * External: `HEAD` -> fallback `GET` on 405/501, follow redirects, configurable timeout.
   * Internal: resolve relative to source file, check `Path.exists()`.
4. **Concurrency:** Thread pool, default 10 workers, configurable.
5. **Reporting:** stdout table + summary `checked/passed/failed/skipped`. Exit code `0` clean, `1` broken found, `2` usage/error.

## 3. CLI Schema
```
mdcheck --file README.md | --dir ./docs [-r]
  [--timeout 5.0] [--concurrency 10]
  [--ignore-external] [--ignore-internal]
  [--exclude PATTERN ...] [--allow-status 200,301...]
  [--output text|json] [-v|--verbose] [--version]
```

| Flag | Type | Default | Description |
|---|---|---|---|
| `--file` | `Path` | — | Single `.md` file. Mutually exclusive with `--dir`. One required. |
| `--dir` | `Path` | — | Directory to scan for `*.md`. |
| `-r, --recursive` | `bool` | `False` | Recurse `--dir`. |
| `--timeout` | `float` | `5.0` | Per-request seconds. |
| `--concurrency` | `int` | `10` | Max workers, 1-50. |
| `--ignore-external` | `bool` | `False` | Skip http/https checks. |
| `--ignore-internal` | `bool` | `False` | Skip relative path checks. |
| `--exclude` | `str[]` | `[]` | Regex to skip URLs. Repeatable. |
| `--allow-status` | `int[]` | `200-299` | Additional accepted codes, e.g. `403`. |
| `--output` | `enum` | `text` | `text` or `json` to stdout. |
| `-v` | `count` | `0` | Verbosity. |

## 4. Module Architecture
```
src/mdcheck/
  __init__.py  # package marker
  cli.py       # CliConfig dataclass, argparse build, main() orchestration, exit codes
  parser.py    # MarkdownLinkParser class: parse_file(path)->list[Link], Link{url, file, line, kind}
  checker.py   # LinkChecker class: check(links)->list[Result], Result{link, ok, status|error}
  reporter.py  # Reporter class: to_text(), to_json()
```

| Class | Responsibility | Key Methods |
|---|---|---|
| `MarkdownLinkParser` | Regex + ref-map extraction, strip code fences | `parse_file()`, `parse_text()` |
| `LinkChecker` | `requests.Session` reuse, `ThreadPoolExecutor` map | `check_link()`, `check_all()` |
| `CliConfig` | Validated args dataclass | `from_args()` |
| `Reporter` | Formatting only, no I/O logic | `format()` |

Dependencies: stdlib + `requests` only (runtime). Python >=3.10. Layout root: `src/mdcheck/` (all imports as `mdcheck.*`).

## 5. Testing Strategy (PyTest)
Target **>=85% coverage** for `parser.py`, `checker.py`; **>=70%** overall.

* `tests/test_parser.py`: inline, reference, autolink, bare URL, ignores code block, line numbers, dedup. No network.
* `tests/test_checker.py`: mock HTTP via stdlib `unittest.mock` only (no `responses` / `requests-mock` / `pytest-mock`):
  * `mock_session_200`, `mock_session_404`, `mock_timeout`, `mock_redirect`, `mock_head_fallback` (HEAD 405 -> GET 200).
  * Internal: `tmp_path` fixture with real files.
* `tests/test_cli.py`: `capsys` + `tmp_path`, exit codes 0/1/2, `--ignore-external`, `--output json` schema, `--exclude` filtering.
* Fixtures in `tests/conftest.py`: `sample_md()`, `mock_session()`.
* Run: `pytest -q --cov=mdcheck --cov-fail-under=70`
