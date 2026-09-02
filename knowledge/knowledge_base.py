import json
from pathlib import Path
from typing import Any

_DEFAULT_PATH = Path(__file__).parent / "domains.json"


class KnowledgeBase:
    def __init__(self, path: Path = _DEFAULT_PATH) -> None:
        self._data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    def retrieve(self, key: str) -> dict[str, Any]:
        """Return domain config for the given agent key, or an empty dict."""
        return self._data.get(key, {})
