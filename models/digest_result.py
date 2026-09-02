from dataclasses import dataclass, field


@dataclass
class DigestResult:
    message: str
    urls: list[str]
    stats: dict[str, int] = field(default_factory=dict)
