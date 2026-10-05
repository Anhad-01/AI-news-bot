from abc import ABC, abstractmethod
from datetime import datetime

from models.feed_article import FeedArticle


class ArticleRanker(ABC):
    """
    Pluggable ranking interface for FeedArticle lists.

    Swap the implementation passed to BaseNewsAgent without touching any agent code.
    Examples of future rankers: RelevanceRanker, EngagementRanker, HybridRanker.
    """

    @abstractmethod
    def rank(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        """Return articles sorted by priority, highest first."""


class ChronologicalRanker(ArticleRanker):
    """
    Ranks articles newest-first.
    Articles with no publish date are placed at the end.
    """

    def rank(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        return sorted(
            articles,
            key=lambda a: a.published or datetime.min,
            reverse=True,
        )
