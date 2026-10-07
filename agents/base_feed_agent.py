from abc import ABC, abstractmethod

from agents.base_agent import BaseAgent
from knowledge.knowledge_base import KnowledgeBase
from models.agent_response import AgentResponse, AgentStatus, ArticleSummary
from models.feed_article import FeedArticle
from services.article_classifier import ArticleClassifier
from services.article_ranker import ArticleRanker
from services.llm_service import LLMService
from services.rss_service import RSSService
from services.url_tracker import SeenURLs, normalized_url


class BaseFeedAgent(BaseAgent, ABC):
    """
    Shared lifecycle for every agent that reads RSS feeds.

    Lifecycle (execute):
        Fetch from RSS feed(s) → prepare (exclude + classify) → rank by date
        → claim unseen URLs → summarize

    Per-agent config (knowledge/domains.json):
        feeds.primary / feeds.fallback   RSS feed URLs (fallback is optional)
        batch_size                       Entries fetched from each feed per request
        exclude_text_signals             Entries containing any of these strings are dropped

    Tier base classes set `default_batch_size` and may override `_prepare_articles()`.
    """

    default_batch_size: int

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

    def execute(self, max_results: int, seen_urls: SeenURLs) -> AgentResponse:
        articles = self._prepare_articles(self._fetch_articles(offset=0))
        ranked = self._ranker.rank(articles)

        # claim() is atomic, so agents running in parallel never pick the same URL.
        selected: list[FeedArticle] = []
        for article in ranked:
            if len(selected) >= max_results:
                break
            if seen_urls.claim(normalized_url(article.url)):
                selected.append(article)

        return AgentResponse(
            agent_name=self.get_agent_name(),
            articles=[self._summarize(a) for a in selected],
            status=AgentStatus.SUCCESS,
        )

    # ── overridable hooks ─────────────────────────────────────────────────────

    def _prepare_articles(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        """Drop excluded entries, then run the classifier (currently a pass-through)."""
        signals = self._domain_config.get("exclude_text_signals", [])
        kept = [a for a in articles if not any(s in a.content for s in signals)]
        return self._classifier.classify(kept)

    # ── shared helpers ────────────────────────────────────────────────────────

    @property
    def _batch_size(self) -> int:
        return self._domain_config.get("batch_size", self.default_batch_size)

    def _fetch_articles(self, offset: int) -> list[FeedArticle]:
        """Fetch one batch from the primary feed and (if configured) the fallback feed."""
        feeds = self._domain_config.get("feeds", {})
        return (
            self._rss.fetch(feeds.get("primary", ""), offset=offset, count=self._batch_size)
            + self._rss.fetch(feeds.get("fallback", ""), offset=offset, count=self._batch_size)
        )

    def _summarize(self, article: FeedArticle) -> ArticleSummary:
        prompt = self.build_summary_prompt(article)
        summary = self._llm.generate(prompt)
        return ArticleSummary(
            title=article.title,
            url=normalized_url(article.url),
            summary=summary,
            topic=self.get_agent_name(),
        )
