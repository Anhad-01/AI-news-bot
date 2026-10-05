from agents.news.base_news_agent import BaseNewsAgent
from config import Config
from models.feed_article import FeedArticle
from prompts.news.defence_prompt import DEFENCE_SUMMARY_PROMPT


class DefenceNewsAgent(BaseNewsAgent):
    def get_agent_name(self) -> str:
        return "Defence News"

    def get_knowledge_key(self) -> str:
        return "defence_news"

    def build_summary_prompt(self, article: FeedArticle) -> str:
        return DEFENCE_SUMMARY_PROMPT.format(
            title=article.title,
            url=article.url,
            source_text=article.content[: Config.MAX_CONTENT_CHARS],
        )
