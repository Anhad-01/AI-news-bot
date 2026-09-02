from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class ArticleSummary:
    title: str
    url: str
    summary: str
    topic: str


@dataclass
class AgentResponse:
    agent_name: str
    articles: list[ArticleSummary]
    status: AgentStatus
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_success(self) -> bool:
        return self.status == AgentStatus.SUCCESS


@dataclass
class AgentExecutionResult:
    agent_name: str
    status: AgentStatus
    attempts: int
    execution_time: float
    error_message: str | None = None
