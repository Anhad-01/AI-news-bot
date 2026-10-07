from agents.research.base_research_agent import BaseResearchAgent
from models.feed_article import FeedArticle
from prompts.research.agentic_ai_prompt import AGENTIC_AI_SUMMARY_PROMPT


class AgenticAIResearchAgent(BaseResearchAgent):
    def get_agent_name(self) -> str:
        return "Agentic AI Research"

    def get_knowledge_key(self) -> str:
        return "agentic_ai_research"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return AGENTIC_AI_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_label="Abstract",
            source_text=self.extract_abstract(article),
        )
