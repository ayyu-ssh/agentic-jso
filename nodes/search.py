import logging
from concurrent.futures import ThreadPoolExecutor

from tavily import TavilyClient

from utils.config import TAVILY_API_KEY
from utils.schema import AgenticJSOSharedState

logger = logging.getLogger("agentic_jso_api")

_tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def search_tavily(query: str) -> list[dict]:
    try:
        response = _tavily_client.search(
            query=query,
            search_depth="basic",
            max_results=10,
        )
        return response.get("results", [])
    except Exception as exc:
        logger.error("Tavily search error: %s | query: %s", exc, query[:120])
        return []


def run_parallel_search(state: AgenticJSOSharedState) -> AgenticJSOSharedState:

    xray_queries = state.xray_queries
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(search_tavily, q) for q in xray_queries.values()]
        for f in futures:
            results.extend(f.result())

    def deduplicate(items: list[dict]) -> list[dict]:
        seen: set[str] = set()
        unique = []
        for r in items:
            url = r.get("url")
            if url and url not in seen:
                seen.add(url)
                unique.append(r)
        return unique

    state.search_results = deduplicate(results)
    logger.info(
        "Search completed: %d unique results from %d queries",
        len(state.search_results),
        len(xray_queries),
    )

    return state