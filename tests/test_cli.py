"""CLI tests per SPEC.md §3, §5 — TDD red phase.

Expected interface:
  from mdcheck.cli import CliConfig, main
  CliConfig.from_args(args_list: list[str]) -> CliConfig
  main(args_list: list[str] | None = None) -> int  (0 clean, 1 broken, 2 error)

No src/mdcheck/cli.py exists yet — these must FAIL.
Uses stdlib unittest.mock only; internal-link fixtures avoid real HTTP.
"""
import json
from unittest import mock

from mdcheck.cli import CliConfig, main


def _write(path, content):
    path.write_text(content, encoding="utf-8")
    return str(path)


def _mock_resp(status):
    r = mock.MagicMock()
    r.status_code = status
    return r


def test_from_args_defaults(tmp_path):
    f = tmp_path / "doc.md"
    f.write_text("# hi\n", encoding="utf-8")
    cfg = CliConfig.from_args(["--file", str(f)])
    assert cfg.timeout == 5.0
    assert cfg.concurrency == 10
    assert cfg.output == "text"


def test_file_exit_0_valid_internal(tmp_path, capsys):
    target = tmp_path / "target.md"
    target.write_text("# t\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    _write(doc, "[T](target.md)\n")
    assert main(["--file", str(doc)]) == 0


def test_file_exit_1_broken_internal(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    _write(doc, "[T](nope.md)\n")
    assert main(["--file", str(doc)]) == 1


def test_missing_args_exit_2(capsys):
    assert main([]) == 2


def test_dir_non_recursive(tmp_path, capsys):
    _write(tmp_path / "a.md", "[T](nope.md)\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub / "b.md", "[T](nope2.md)\n")
    # Non-recursive: only top-level broken link -> exit 1 (same either way here,
    # but implementation must support --dir without -r).
    assert main(["--dir", str(tmp_path)]) == 1


def test_dir_recursive(tmp_path, capsys):
    _write(tmp_path / "a.md", "# clean, no links\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub / "b.md", "[T](nope.md)\n")
    # Without -r the broken nested file is skipped -> exit 0.
    assert main(["--dir", str(tmp_path)]) == 0
    # With -r the nested broken link is found -> exit 1.
    assert main(["--dir", str(tmp_path), "-r"]) == 1


def test_ignore_external(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    _write(doc, "[E](https://example.com/broken)\n")
    with mock.patch("requests.Session") as cls:
        cls.return_value.head.return_value = _mock_resp(404)
        assert main(["--file", str(doc)]) == 1
        assert main(["--file", str(doc), "--ignore-external"]) == 0


def test_ignore_internal(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    _write(doc, "[T](nope.md)\n")
    assert main(["--file", str(doc), "--ignore-internal"]) == 0


def test_exclude_pattern(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    _write(doc, "[E](https://excluded.example.com/bad)\n")
    with mock.patch("requests.Session") as cls:
        cls.return_value.head.return_value = _mock_resp(404)
        assert main(["--file", str(doc)]) == 1
        assert main(["--file", str(doc), "--exclude", "excluded"]) == 0


def test_output_json_schema(tmp_path, capsys):
    target = tmp_path / "target.md"
    target.write_text("# t\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    _write(doc, "[T](target.md)\n")
    assert main(["--file", str(doc), "--output", "json"]) == 0
    out = capsys.readouterr().out
    json.loads(out)
