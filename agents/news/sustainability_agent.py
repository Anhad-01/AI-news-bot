from agents.news.base_news_agent import BaseNewsAgent
from config import Config
from models.feed_article import FeedArticle
from prompts.news.sustainability_prompt import SUSTAINABILITY_SUMMARY_PROMPT


class SustainabilityNewsAgent(BaseNewsAgent):
    def get_agent_name(self) -> str:
        return "Sustainability News"

    def get_knowledge_key(self) -> str:
        return "sustainability_news"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return SUSTAINABILITY_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_text=article.content[: Config.MAX_CONTENT_CHARS],
        )
