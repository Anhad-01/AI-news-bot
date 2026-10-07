from datetime import datetime
from html.parser import HTMLParser
from time import mktime
import html as html_module

import feedparser

from models.feed_article import FeedArticle


class _HTMLStripper(HTMLParser):
    """Minimal HTMLParser that collects visible text nodes."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts).strip()


def _strip_html(raw: str) -> str:
    raw = html_module.unescape(raw)
    stripper = _HTMLStripper()
    stripper.feed(raw)
    return stripper.get_text()


class RSSService:
    """
    Parses RSS / Atom feeds and returns slices of articles as FeedArticle objects.

    Uses feedparser for robust handling of date formats, encoding, and feed dialects.
    Each call to fetch() is stateless — no caching between calls.
    """

    def fetch(self, feed_url: str, offset: int = 0, count: int = 2) -> list[FeedArticle]:
        """
        Return `count` articles from `feed_url` starting at `offset`.

        Returns an empty list on network failure, parse error, or empty feed
        so callers can handle the absence of results without exceptions.
        """
        if not feed_url:
            return []

        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            return []

        entries = feed.entries[offset: offset + count]
        return [self._parse_entry(entry) for entry in entries]

    # ── private ──────────────────────────────────────────────────────────────

    def _parse_entry(self, entry: feedparser.FeedParserDict) -> FeedArticle:  # type: ignore[name-defined]
        return FeedArticle(
            title=entry.get("title", "Untitled"),
            url=entry.get("link", ""),
            published=self._parse_date(entry),
            content=self._extract_content(entry),
        )

    def _parse_date(self, entry: feedparser.FeedParserDict) -> datetime | None:  # type: ignore[name-defined]
        for field in ("published_parsed", "updated_parsed"):
            value = entry.get(field)
            if value:
                try:
                    return datetime.fromtimestamp(mktime(value))
                except (ValueError, OverflowError, OSError):
                    continue
        return None

    def _extract_content(self, entry: feedparser.FeedParserDict) -> str:  # type: ignore[name-defined]
        # Prefer full body (content[0]) over excerpt (summary).
        content_list = entry.get("content", [])
        if content_list:
            raw = content_list[0].get("value", "")
        else:
            raw = entry.get("summary", "")
        return _strip_html(raw or "")
