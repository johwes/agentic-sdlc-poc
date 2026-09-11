"""Link checker per SPEC.md §2, §4."""
import concurrent.futures
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import requests

from .parser import Link


@dataclass
class Result:
    link: Link
    ok: bool
    status_or_error: int | str


class LinkChecker:
    def __init__(
        self,
        timeout: float = 5.0,
        concurrency: int = 10,
        allow_status: list[int] | None = None,
    ) -> None:
        self.timeout = timeout
        self.concurrency = concurrency
        self.allow_status = set(allow_status or [])
        self.session = requests.Session()

    def _accepted(self, status: int) -> bool:
        return 200 <= status <= 299 or status in self.allow_status

    def _check_internal(self, link: Link) -> Result:
        cleaned = urlsplit(link.url).path or link.url.split("#")[0].split("?")[0]
        # Pure anchor (e.g. "#section") refers to the source file itself.
        if not cleaned:
            target = Path(link.file)
        else:
            target = Path(link.file).parent / cleaned
        if target.exists():
            return Result(link=link, ok=True, status_or_error=200)
        return Result(link=link, ok=False, status_or_error="File not found")

    def _check_external(self, link: Link) -> Result:
        try:
            resp = self.session.head(
                link.url, timeout=self.timeout, allow_redirects=True
            )
            if resp.status_code in (405, 501):
                resp = self.session.get(
                    link.url, timeout=self.timeout, allow_redirects=True,
                    stream=True,
                )
            if self._accepted(resp.status_code):
                return Result(link=link, ok=True, status_or_error=resp.status_code)
            return Result(link=link, ok=False, status_or_error=resp.status_code)
        except requests.exceptions.Timeout:
            return Result(link=link, ok=False, status_or_error="Timeout")
        except requests.exceptions.RequestException as e:
            return Result(link=link, ok=False, status_or_error=str(e))

    def check_link(self, link: Link) -> Result:
        if link.kind == "internal":
            return self._check_internal(link)
        return self._check_external(link)

    def check_all(self, links: list[Link]) -> list[Result]:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.concurrency
        ) as executor:
            return list(executor.map(self.check_link, links))
