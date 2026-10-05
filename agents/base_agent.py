from abc import ABC, abstractmethod
from typing import Any

from knowledge.knowledge_base import KnowledgeBase
from models.agent_response import AgentResponse
from services.llm_service import LLMService


class BaseAgent(ABC):
    """
    Minimal abstract contract shared by every agent.

    Each tier base class (BaseResearchAgent, BaseNewsAgent) owns its own
    execute() lifecycle and _summarize() helper, since the two pipelines
    differ fundamentally (Tavily search vs RSS + rank).
    """

    def __init__(self, llm: LLMService, knowledge: KnowledgeBase) -> None:
        self._llm = llm
        self._domain_config: dict[str, Any] = knowledge.retrieve(self.get_knowledge_key())

    @abstractmethod
    def get_agent_name(self) -> str:
        """Human-readable agent identifier."""

    @abstractmethod
    def get_knowledge_key(self) -> str:
        """Key used to look up this agent's config in the KnowledgeBase."""

    @abstractmethod
    def execute(self, max_results: int, seen_urls: set[str]) -> AgentResponse:
        """Full execution lifecycle — implemented by each tier base class."""
