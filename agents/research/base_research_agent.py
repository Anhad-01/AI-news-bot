import re
from abc import ABC
from typing import Any

from agents.base_agent import BaseAgent
from config import Config

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
    Shared behaviour for all research agents:
    - Tavily search restricted to academic domains with a one-week window.
    - Two-stage filter: domain allowlist, then URL/text signal check.
    - Abstract extraction for richer LLM context.
    """

    def get_search_params(self) -> dict[str, Any]:
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
        allowed = self._domain_config.get("allowed_domains", _FALLBACK_DOMAINS)
        strong = set(self._domain_config.get("strong_domains", []))
        url_signals = self._domain_config.get("url_signals", list(_FALLBACK_URL_SIGNALS))
        text_signals = self._domain_config.get("text_signals", list(_FALLBACK_TEXT_SIGNALS))

        # Must come from an allowed domain (exact match or subdomain).
        if not any(domain == d or domain.endswith(f".{d}") for d in allowed):
            return False

        # Trusted academic sources pass automatically.
        if domain in strong:
            return True

        # For other allowed domains, require at least one quality signal.
        content = article.get("raw_content") or article.get("content") or ""
        text = f"{article.get('title', '')} {content}".lower()

        return any(sig in url.lower() for sig in url_signals) or any(
            sig in text for sig in text_signals
        )

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
