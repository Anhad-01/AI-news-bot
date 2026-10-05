from abc import ABC, abstractmethod

from agents.base_agent import BaseAgent
from config import Config
from knowledge.knowledge_base import KnowledgeBase
from models.agent_response import AgentResponse, AgentStatus, ArticleSummary
from models.feed_article import FeedArticle
from services.article_classifier import ArticleClassifier
from services.article_ranker import ArticleRanker
from services.llm_service import LLMService
from services.rss_service import RSSService
from services.url_tracker import normalized_url


class BaseNewsAgent(BaseAgent, ABC):
    """
    Shared behaviour for all news agents.

    Lifecycle (execute):
        Fetch from RSS feeds → (classifier pass-through) → rank by date
        → deduplicate → summarize

    Classification and the Indian/Global retry loop are wired in as stubs.
    Activate them by:
      1. Implementing ArticleClassifier.classify().
      2. Uncommenting the geography filter block below.
      3. Uncommenting the retry loop block below.
    """

    def __init__(
        self,
        llm: LLMService,
        rss: RSSService,
        classifier: ArticleClassifier,
        ranker: ArticleRanker,
        knowledge: KnowledgeBase,
    ) -> None:
        super().__init__(llm, knowledge)
        self._rss = rss
        self._classifier = classifier
        self._ranker = ranker

    @abstractmethod
    def build_summary_prompt(self, article: FeedArticle) -> str:
        """Build the LLM summarization prompt for a single FeedArticle."""

    # ── template method ───────────────────────────────────────────────────────

    def execute(self, max_results: int, seen_urls: set[str]) -> AgentResponse:
        feeds = self._domain_config.get("feeds", {})
        primary_url: str = feeds.get("primary", "")
        fallback_url: str = feeds.get("fallback", "")
        batch_size: int = self._domain_config.get("batch_size", Config.NEWS_BATCH_SIZE)

        # Fetch top N articles from each feed.
        articles = (
            self._rss.fetch(primary_url, offset=0, count=batch_size)
            + self._rss.fetch(fallback_url, offset=0, count=batch_size)
        )

        # Pass through classifier (currently a no-op).
        # When activated, this sets article.geography on each article.
        articles = self._classifier.classify(articles)

        # ── Activate when classifier is ready ─────────────────────────────
        # max_retries = self._domain_config.get(
        #     "max_classify_retries", Config.NEWS_MAX_CLASSIFY_RETRIES
        # )
        # for attempt in range(1, max_retries + 1):
        #     if any(a.geography == "Indian" for a in articles):
        #         break
        #     offset = attempt * batch_size
        #     new_batch = (
        #         self._rss.fetch(primary_url, offset=offset, count=batch_size)
        #         + self._rss.fetch(fallback_url, offset=offset, count=batch_size)
        #     )
        #     if not new_batch:
        #         break
        #     articles += self._classifier.classify(new_batch)
        #
        # articles = [a for a in articles if a.geography == "Indian"]
        # ──────────────────────────────────────────────────────────────────

        # Rank by publish date, newest first.
        ranked = self._ranker.rank(articles)

        # Deduplicate against previously seen URLs.
        filtered = [
            a for a in ranked if normalized_url(a.url) not in seen_urls
        ][:max_results]

        if not filtered:
            return AgentResponse(
                agent_name=self.get_agent_name(),
                articles=[],
                status=AgentStatus.SUCCESS,
            )

        summaries = [self._summarize(a) for a in filtered]
        return AgentResponse(
            agent_name=self.get_agent_name(),
            articles=summaries,
            status=AgentStatus.SUCCESS,
        )

    # ── private ───────────────────────────────────────────────────────────────

    def _summarize(self, article: FeedArticle) -> ArticleSummary:
        prompt = self.build_summary_prompt(article)
        summary = self._llm.generate(prompt)
        return ArticleSummary(
            title=article.title,
            url=normalized_url(article.url),
            summary=summary,
            topic=self.get_agent_name(),
        )
