import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from agents.base_agent import BaseAgent
from config import Config
from knowledge.knowledge_base import KnowledgeBase
from models.agent_response import AgentResponse, AgentStatus, ArticleSummary
from services.llm_service import LLMService
from services.search_service import SearchService
from services.url_tracker import domain_for_url, normalized_url

_FALLBACK_DOMAINS = [
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov",
    "nature.com", "science.org", "sciencedirect.com", "elsevier.com",
    "springer.com", "aclanthology.org", "openreview.net", "ieee.org",
    "dl.acm.org", "jmlr.org", "proceedings.mlr.press", "biorxiv.org",
    "medrxiv.org",
]
_FALLBACK_URL_SIGNALS = ("/abs/", "/pdf/", "/article/", "/paper/", "/content/", "/doi/")
_FALLBACK_TEXT_SIGNALS = ("abstract", "doi", "journal", "conference", "preprint")


class BaseResearchAgent(BaseAgent, ABC):
    """
    Shared behaviour for all research agents.

    Lifecycle (execute):
        Tavily search → filter by domain + signals → deduplicate → summarize

    Concrete agents must implement:
        get_agent_name(), get_knowledge_key(), get_search_query(), build_summary_prompt()

    Concrete agents may override:
        get_search_params(), filter_article()
    """

    def __init__(
        self,
        llm: LLMService,
        search: SearchService,
        knowledge: KnowledgeBase,
    ) -> None:
        super().__init__(llm, knowledge)
        self._search = search

    # ── abstract hooks ────────────────────────────────────────────────────────

    @abstractmethod
    def get_search_query(self) -> str:
        """Tavily search query string for this topic."""

    @abstractmethod
    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        """Build the LLM summarization prompt for a single article."""

    # ── template method ───────────────────────────────────────────────────────

    def execute(self, max_results: int, seen_urls: set[str]) -> AgentResponse:
        raw = self._search.search(self.get_search_query(), **self.get_search_params())
        selected = self._select_articles(raw, max_results, seen_urls)
        articles = [self._summarize(article) for article in selected]
        return AgentResponse(
            agent_name=self.get_agent_name(),
            articles=articles,
            status=AgentStatus.SUCCESS,
        )

    # ── overridable defaults ──────────────────────────────────────────────────

    def get_search_params(self) -> dict[str, Any]:
        """Tavily search parameters. Override to customise per-agent."""
        domains = self._domain_config.get("allowed_domains", _FALLBACK_DOMAINS)
        return {
            "topic": "general",
            "time_range": "week",
            "include_domains": domains,
            "max_results": Config.SEARCH_RESULTS_PER_TOPIC,
            "include_raw_content": True,
            "search_depth": "basic",
        }

    def filter_article(self, article: dict[str, Any], url: str, domain: str) -> bool:
        """Domain allowlist + URL/text signal filter. Override to customise."""
        allowed = self._domain_config.get("allowed_domains", _FALLBACK_DOMAINS)
        strong = set(self._domain_config.get("strong_domains", []))
        url_signals = self._domain_config.get("url_signals", list(_FALLBACK_URL_SIGNALS))
        text_signals = self._domain_config.get("text_signals", list(_FALLBACK_TEXT_SIGNALS))

        if not any(domain == d or domain.endswith(f".{d}") for d in allowed):
            return False
        if domain in strong:
            return True

        content = article.get("raw_content") or article.get("content") or ""
        text = f"{article.get('title', '')} {content}".lower()
        return any(sig in url.lower() for sig in url_signals) or any(
            sig in text for sig in text_signals
        )

    # ── shared helpers ────────────────────────────────────────────────────────

    def extract_abstract(self, article: dict[str, Any]) -> str:
        """Pull the abstract section from raw article content, if present."""
        content = article.get("raw_content") or article.get("content") or ""
        if not content:
            return ""
        collapsed = re.sub(r"\s+", " ", content).strip()
        match = re.search(
            r"\babstract\b[:\s-]*(.*?)"
            r"(?:\bintroduction\b|\bbackground\b|\bkeywords\b|\breferences\b|$)",
            collapsed,
            flags=re.IGNORECASE,
        )
        if not match:
            return ""
        return match.group(1).strip()[:5_000]

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
