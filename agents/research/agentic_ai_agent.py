from typing import Any

from agents.research.base_research_agent import BaseResearchAgent
from config import Config
from prompts.research.agentic_ai_prompt import AGENTIC_AI_SUMMARY_PROMPT


class AgenticAIResearchAgent(BaseResearchAgent):
    def get_agent_name(self) -> str:
        return "Agentic AI Research"

    def get_knowledge_key(self) -> str:
        return "agentic_ai_research"

    def get_search_query(self) -> str:
        return "latest research articles papers from the past week about agentic AI autonomous agents"

    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        abstract = self.extract_abstract(article)
        source_text = abstract or (
            article.get("raw_content") or article.get("content") or ""
        )[: Config.MAX_CONTENT_CHARS]
        return AGENTIC_AI_SUMMARY_PROMPT.format(
            title=article.get("title") or "Untitled",
            url=article.get("url") or "",
            source_label="Abstract" if abstract else "Article text",
            source_text=source_text,
        )
