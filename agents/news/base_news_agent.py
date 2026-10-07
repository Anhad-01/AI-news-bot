from abc import ABC

from agents.base_feed_agent import BaseFeedAgent
from config import Config
from models.feed_article import FeedArticle


class BaseNewsAgent(BaseFeedAgent, ABC):
    """
    Shared behaviour for all news agents.

    Uses the standard BaseFeedAgent lifecycle. Classification and the
    Indian/Global retry loop are wired in as stubs in _prepare_articles().
    Activate them by:
      1. Implementing ArticleClassifier.classify().
      2. Uncommenting the retry loop and geography filter below.
    """

    default_batch_size = Config.NEWS_BATCH_SIZE

    def _prepare_articles(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        # Excludes entries and runs the classifier (currently a no-op).
        # When activated, the classifier sets article.geography on each article.
        articles = super()._prepare_articles(articles)

        # ── Activate when classifier is ready ─────────────────────────────
        # max_retries = self._domain_config.get(
        #     "max_classify_retries", Config.NEWS_MAX_CLASSIFY_RETRIES
        # )
        # for attempt in range(1, max_retries + 1):
        #     if any(a.geography == "Indian" for a in articles):
        #         break
        #     new_batch = self._fetch_articles(offset=attempt * self._batch_size)
        #     if not new_batch:
        #         break
        #     articles += super()._prepare_articles(new_batch)
        #
        # articles = [a for a in articles if a.geography == "Indian"]
        # ──────────────────────────────────────────────────────────────────

        return articles
