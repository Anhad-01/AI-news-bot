from typing import Any

from agents.research.base_research_agent import BaseResearchAgent
from config import Config
from prompts.research.nlp_prompt import NLP_SUMMARY_PROMPT


class NLPResearchAgent(BaseResearchAgent):
    def get_agent_name(self) -> str:
        return "NLP Research"

    def get_knowledge_key(self) -> str:
        return "nlp_research"

    def get_search_query(self) -> str:
        return "latest research articles papers from the past week about natural language processing NLP"

    def build_summary_prompt(self, article: dict[str, Any]) -> str:
        abstract = self.extract_abstract(article)
        source_text = abstract or (
            article.get("raw_content") or article.get("content") or ""
        )[: Config.MAX_CONTENT_CHARS]
        return NLP_SUMMARY_PROMPT.format(
            title=article.get("title") or "Untitled",
            url=article.get("url") or "",
            source_label="Abstract" if abstract else "Article text",
            source_text=source_text,
        )
