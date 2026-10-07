from agents.research.base_research_agent import BaseResearchAgent
from models.feed_article import FeedArticle
from prompts.research.nlp_prompt import NLP_SUMMARY_PROMPT


class NLPResearchAgent(BaseResearchAgent):
    """Currently inactive — not listed in _RESEARCH_AGENTS in main.py."""

    def get_agent_name(self) -> str:
        return "NLP Research"

    def get_knowledge_key(self) -> str:
        return "nlp_research"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return NLP_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_label="Abstract",
            source_text=self.extract_abstract(article),
        )
