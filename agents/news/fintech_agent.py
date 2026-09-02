from typing import Any

from agents.news.base_news_agent import BaseNewsAgent
from config import Config
from prompts.news.fintech_prompt import FINTECH_SUMMARY_PROMPT


class FintechNewsAgent(BaseNewsAgent):
    def get_agent_name(self) -> str:
        return "Fintech News"

    def get_knowledge_key(self) -> str:
        return "fintech_news"

    def get_search_query(self) -> str:
        return "latest fintech finance banking cryptocurrency payments news today"

    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        source_text = (
            article.get("raw_content") or article.get("content") or ""
        )[: Config.MAX_CONTENT_CHARS]
        return FINTECH_SUMMARY_PROMPT.format(
            title=article.get("title") or "Untitled",
            url=article.get("url") or "",
            source_text=source_text,
        )
