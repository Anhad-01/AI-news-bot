from typing import Any

from agents.news.base_news_agent import BaseNewsAgent
from config import Config
from prompts.news.defence_prompt import DEFENCE_SUMMARY_PROMPT


class DefenceNewsAgent(BaseNewsAgent):
    def get_agent_name(self) -> str:
        return "Defence News"

    def get_knowledge_key(self) -> str:
        return "defence_news"

    def get_search_query(self) -> str:
        return "latest defence military geopolitics conflict news today"

    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        source_text = (
            article.get("raw_content") or article.get("content") or ""
        )[: Config.MAX_CONTENT_CHARS]
        return DEFENCE_SUMMARY_PROMPT.format(
            title=article.get("title") or "Untitled",
            url=article.get("url") or "",
            source_text=source_text,
        )
