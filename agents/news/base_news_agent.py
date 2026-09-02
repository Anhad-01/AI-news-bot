from abc import ABC
from typing import Any

from agents.base_agent import BaseAgent
from config import Config


class BaseNewsAgent(BaseAgent, ABC):
    """
    Shared behaviour for all news agents:
    - Tavily news search with a one-day window.
    - No domain allowlist — deduplication is handled by the base class.
    """

    def get_search_params(self) -> dict[str, Any]:
        return {
            "topic": "news",
            "time_range": "day",
            "days": 1,
            "max_results": Config.SEARCH_RESULTS_PER_TOPIC,
            "include_raw_content": True,
            "search_depth": "basic",
        }

    def filter_article(self, article: dict[str, Any], url: str, domain: str) -> bool:
        # News agents accept any domain; source diversity is enforced by the
        # per-domain deduplication cap in BaseAgent._select_articles().
        return True
