from agents.research.base_research_agent import BaseResearchAgent
from config import Config
from models.feed_article import FeedArticle
from prompts.research.etech_prompt import ETECH_SUMMARY_PROMPT


class ETechResearchAgent(BaseResearchAgent):
    def get_agent_name(self) -> str:
        return "ETech"

    def get_knowledge_key(self) -> str:
        return "etech_research"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return ETECH_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_text=article.content[: Config.MAX_CONTENT_CHARS],
        )
