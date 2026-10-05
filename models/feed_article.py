from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeedArticle:
    title: str
    url: str
    published: datetime | None  # parsed from RSS; None if the feed omits it
    content: str                # HTML-stripped text from description or full body
    geography: str | None = None  # "Indian" | "Global" | None (unclassified)
