import re
from abc import ABC

from agents.base_feed_agent import BaseFeedAgent
from config import Config
from models.feed_article import FeedArticle

_ABSTRACT_PATTERN = re.compile(r"\babstract:\s*(.*)", flags=re.IGNORECASE | re.DOTALL)


class BaseResearchAgent(BaseFeedAgent, ABC):
    """
    Shared behaviour for all research agents.

    Uses the standard BaseFeedAgent lifecycle; the classifier stays a pass-through
    and there is no retry loop.
    """

    default_batch_size = Config.RESEARCH_BATCH_SIZE

    def extract_abstract(self, article: FeedArticle) -> str:
        """
        Return the abstract text from a feed entry.

        arXiv feeds prefix the description with "arXiv:<id> Announce Type: ... Abstract: ".
        Falls back to the full entry content when no abstract marker is present.
        """
        content = re.sub(r"\s+", " ", article.content).strip()
        match = _ABSTRACT_PATTERN.search(content)
        text = match.group(1).strip() if match else content
        return text[: Config.MAX_CONTENT_CHARS]
