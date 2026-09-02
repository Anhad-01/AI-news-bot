from typing import Any

from agents.research.base_research_agent import BaseResearchAgent
from config import Config
from prompts.research.ml_prompt import ML_SUMMARY_PROMPT


class MLResearchAgent(BaseResearchAgent):
    def get_agent_name(self) -> str:
        return "ML Research"

    def get_knowledge_key(self) -> str:
        return "ml_research"

    def get_search_query(self) -> str:
        return "latest research articles papers from the past week about machine learning"

    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        abstract = self.extract_abstract(article)
        source_text = abstract or (
            article.get("raw_content") or article.get("content") or ""
        )[: Config.MAX_CONTENT_CHARS]
        return ML_SUMMARY_PROMPT.format(
            title=article.get("title") or "Untitled",
            url=article.get("url") or "",
            source_label="Abstract" if abstract else "Article text",
            source_text=source_text,
        )
