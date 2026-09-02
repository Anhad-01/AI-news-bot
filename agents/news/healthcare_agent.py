from typing import Any

from agents.news.base_news_agent import BaseNewsAgent
from config import Config
from prompts.news.healthcare_prompt import HEALTHCARE_SUMMARY_PROMPT


class HealthcareNewsAgent(BaseNewsAgent):
    def get_agent_name(self) -> str:
        return "Healthcare News"

    def get_knowledge_key(self) -> str:
        return "healthcare_news"

    def get_search_query(self) -> str:
        return "latest healthcare medicine public health news today"

    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        source_text = (
            article.get("raw_content") or article.get("content") or ""
        )[: Config.MAX_CONTENT_CHARS]
        return HEALTHCARE_SUMMARY_PROMPT.format(
            title=article.get("title") or "Untitled",
            url=article.get("url") or "",
            source_text=source_text,
        )
