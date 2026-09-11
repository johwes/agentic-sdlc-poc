# AGENTS.md — Agent Working Agreement

Source of truth: `SPEC.md`. Do not diverge without human approval.

## Rule 1 — TDD First
1. Write/update `tests/test_*.py` first per SPEC.md §5.
2. Then implement minimal `src/` logic to pass.
3. No src logic without failing test first.

Layout:
- `tests/test_parser.py`, `tests/test_checker.py`, `tests/test_cli.py`, `tests/conftest.py`
- `src/mdcheck/parser.py`, `checker.py`, `cli.py`, `reporter.py`

## Rule 2 — Scope Lock
- Strictly adhere to `SPEC.md` §2-4 interfaces: `MarkdownLinkParser.parse_file()`, `LinkChecker.check_all()`, CLI flags in §3.
- Runtime deps: `stdlib + requests` only, Python >=3.10. Dev deps: `pytest + pytest-cov` only — use stdlib `unittest.mock` for HTTP mocks, no `requests-mock` / `responses` / `pytest-mock`.
- All modules live in `src/mdcheck/` per SPEC.md §4 — never write to repo root.
- If SPEC ambiguous, ask human — do not invent API.

## Rule 3 — Self-Correction
1. After generation: run `pytest -q --cov=mdcheck --cov-fail-under=70`.
2. On failure: diagnose, fix, re-run. Max 3 iterations.
3. After 3rd failure: stop, paste last error + diff tried, ask human.
4. Never commit with red tests. No networked tests — use mocks per SPEC.md §5.
