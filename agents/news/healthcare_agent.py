from agents.news.base_news_agent import BaseNewsAgent
from config import Config
from models.feed_article import FeedArticle
from prompts.news.healthcare_prompt import HEALTHCARE_SUMMARY_PROMPT


class HealthcareNewsAgent(BaseNewsAgent):
    def get_agent_name(self) -> str:
        return "Healthcare News"

    def get_knowledge_key(self) -> str:
        return "healthcare_news"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return HEALTHCARE_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_text=article.content[: Config.MAX_CONTENT_CHARS],
        )
