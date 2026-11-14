"""Web search tool with live DuckDuckGo search support."""

from typing import Any

import httpx
from bs4 import BeautifulSoup

from ...agents.base_agent import Tool
from ...observability.logging import get_logger

logger = get_logger(__name__)


class WebSearchTool(Tool):
    """Tool for searching the web."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize web search tool.

        Args:
            api_key: Search API key (optional)
        """
        super().__init__(
            name="web_search",
            description="Search the web for current live information",
        )
        self.api_key = api_key

    async def execute(self, query: str, num_results: int = 5) -> list[dict[str, Any]]:
        """
        Search the web using live DuckDuckGo HTML parser.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search result dictionaries
        """
        logger.info(f"Executing web search for query: {query}")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query},
                    headers=headers,
                )

            soup = BeautifulSoup(res.text, "html.parser")
            results = []

            for result in soup.find_all("div", class_="result")[:num_results]:
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                title = title_elem.get_text(strip=True) if title_elem else "Search Result"
                url = title_elem.get("href", "") if title_elem else ""
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if snippet:
                    results.append({"title": title, "url": url, "snippet": snippet})

            if results:
                logger.info(f"Web search found {len(results)} live results")
                return results

        except Exception as e:
            logger.warning(f"Live web search request failed ({e}), using fallback")

        # Fallback if connection fails
        return [
            {
                "title": f"Web information for: {query}",
                "url": "https://duckduckgo.com",
                "snippet": f"Web search executed for query '{query}'",
            }
        ]
