"""Result reporter per SPEC.md §2, §4."""
import json

from .checker import Result


class Reporter:
    @staticmethod
    def to_text(results: list[Result], verbose: int = 0) -> str:
        checked = len(results)
        passed = sum(1 for r in results if r.ok)
        failed = checked - passed
        lines = []
        for r in results:
            if r.ok or verbose > 0:
                status = "PASS" if r.ok else "FAIL"
                lines.append(
                    f"{status} {r.link.url} "
                    f"({r.link.file}:{r.link.line}) "
                    f"[{r.status_or_error}]"
                )
        lines.append(f"Checked: {checked} | Passed: {passed} | Failed: {failed}")
        return "\n".join(lines)

    @staticmethod
    def to_json(results: list[Result]) -> str:
        payload = [
            {
                "url": r.link.url,
                "file": r.link.file,
                "line": r.link.line,
                "kind": r.link.kind,
                "ok": r.ok,
                "status_or_error": r.status_or_error,
            }
            for r in results
        ]
        return json.dumps(payload, indent=2)
