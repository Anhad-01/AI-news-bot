from typing import Any

from tavily import TavilyClient


class SearchService:
    def __init__(self, api_key: str) -> None:
        self._client = TavilyClient(api_key=api_key)

    def search(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        response = self._client.search(query=query, **kwargs)
        return response.get("results", [])
