from agents.research.base_research_agent import BaseResearchAgent
from models.feed_article import FeedArticle
from prompts.research.computer_vision_prompt import COMPUTER_VISION_SUMMARY_PROMPT


class ComputerVisionResearchAgent(BaseResearchAgent):
    def get_agent_name(self) -> str:
        return "Computer Vision Research"

    def get_knowledge_key(self) -> str:
        return "computer_vision_research"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return COMPUTER_VISION_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_label="Abstract",
            source_text=self.extract_abstract(article),
        )
