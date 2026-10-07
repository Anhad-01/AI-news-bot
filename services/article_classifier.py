from models.feed_article import FeedArticle
from services.llm_service import LLMService


class ArticleClassifier:
    """
    Classifies article headlines as "Indian" or "Global" using an LLM.

    Currently a pass-through skeleton. The classify() method returns articles
    unchanged with geography=None. No LLM calls are made.

    To activate:
      1. Implement the classify() body using CLASSIFICATION_PROMPT.
      2. Uncomment the retry loop and geography filter in
         BaseNewsAgent._prepare_articles().

    Planned implementation (when activated):
      - Build a numbered list of all headlines.
      - Single LLM call with temperature=0.1 for consistency.
      - Parse JSON response → set article.geography for each item.
      - On JSON parse failure: retry once, then fall back to geography="Indian"
        (optimistic — better to summarise a borderline article than miss Indian news).
    """

    def __init__(self, llm: LLMService) -> None:
        self._llm = llm

    def classify(self, articles: list[FeedArticle]) -> list[FeedArticle]:
        # TODO: implement when API key is available.
        return articles
