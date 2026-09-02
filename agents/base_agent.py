from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from knowledge.knowledge_base import KnowledgeBase
from models.agent_response import AgentResponse, AgentStatus, ArticleSummary
from services.llm_service import LLMService
from services.search_service import SearchService
from services.url_tracker import domain_for_url, normalized_url


class BaseAgent(ABC):
    def __init__(
        self,
        llm: LLMService,
        search: SearchService,
        knowledge: KnowledgeBase,
    ) -> None:
        self._llm = llm
        self._search = search
        self._domain_config = knowledge.retrieve(self.get_knowledge_key())

    # ── hooks — implemented by concrete agents ───────────────────────────────

    @abstractmethod
    def get_agent_name(self) -> str:
        """Human-readable agent identifier."""

    @abstractmethod
    def get_knowledge_key(self) -> str:
        """Key used to look up this agent's config in the KnowledgeBase."""

    @abstractmethod
    def get_search_query(self) -> str:
        """Tavily search query for this agent's topic."""

    @abstractmethod
    def get_search_params(self) -> dict[str, Any]:
        """Extra keyword arguments forwarded to SearchService.search()."""

    @abstractmethod
    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        """Build the LLM prompt for a single article."""

    @abstractmethod
    def filter_article(self, article: dict[str, Any], url: str, domain: str) -> bool:
        """Return True if the article passes topic-specific quality filters."""

    # ── template method — never overridden ──────────────────────────────────

    def execute(self, max_results: int, seen_urls: set[str]) -> AgentResponse:
        """
        Full execution lifecycle:
        search → filter → select → summarize → AgentResponse.

        Raises on any unrecoverable error so the orchestrator can retry.
        """
        raw = self._search.search(self.get_search_query(), **self.get_search_params())
        selected = self._select_articles(raw, max_results, seen_urls)
        articles = [self._summarize(article) for article in selected]
        return AgentResponse(
            agent_name=self.get_agent_name(),
            articles=articles,
            status=AgentStatus.SUCCESS,
        )

    # ── private helpers ──────────────────────────────────────────────────────

    def _select_articles(
        self,
        results: list[dict[str, Any]],
        max_results: int,
        seen_urls: set[str],
    ) -> list[dict[str, Any]]:
        run_urls: set[str] = set()
        domain_counts: Counter[str] = Counter()
        selected: list[dict[str, Any]] = []

        for article in results:
            url = normalized_url(article.get("url", ""))
            if not url or url in seen_urls or url in run_urls:
                continue

            domain = domain_for_url(url)

            if not self.filter_article(article, url, domain):
                continue

            # One article per domain per agent run to ensure source diversity.
            if domain_counts[domain] >= 1:
                continue

            selected.append(article)
            run_urls.add(url)
            domain_counts[domain] += 1

            if len(selected) >= max_results:
                break

        return selected

    def _summarize(self, article: dict[str, Any]) -> ArticleSummary:
        prompt = self.build_summary_prompt(article)
        summary = self._llm.generate(prompt)
        return ArticleSummary(
            title=article.get("title") or "Untitled",
            url=normalized_url(article.get("url", "")),
            summary=summary,
            topic=self.get_agent_name(),
        )
