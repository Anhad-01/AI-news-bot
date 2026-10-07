import json
import threading
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_PARAMS = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref"}


def normalized_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    query_items = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in _TRACKING_PARAMS
    ]
    return urlunsplit((scheme, netloc, path, urlencode(query_items), ""))


def domain_for_url(url: str) -> str:
    netloc = urlsplit(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


class SeenURLs(set[str]):
    """
    A set of normalized URLs shared by all agents in one run.

    claim() atomically checks and adds a URL, so agents running in parallel
    can never both select the same article.
    """

    def __init__(self, urls: Iterable[str] = ()) -> None:
        super().__init__(urls)
        self._lock = threading.Lock()

    def claim(self, url: str) -> bool:
        """Return True and record the URL if it was unseen; False otherwise."""
        if not url:
            return False
        with self._lock:
            if url in self:
                return False
            self.add(url)
            return True


class URLTracker:
    def __init__(self, state_dir: Path) -> None:
        self._path = state_dir / "seen_urls.json"

    def load(self) -> SeenURLs:
        if not self._path.exists():
            return SeenURLs()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return SeenURLs()
        if isinstance(data, list):
            return SeenURLs(item for item in data if isinstance(item, str))
        return SeenURLs()

    def mark_seen(self, urls: Iterable[str]) -> None:
        seen = self.load()
        seen.update(url for url in urls if url)
        self._path.parent.mkdir(exist_ok=True)
        self._path.write_text(json.dumps(sorted(seen), indent=2), encoding="utf-8")
