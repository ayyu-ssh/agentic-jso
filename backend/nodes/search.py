import logging
from concurrent.futures import ThreadPoolExecutor

import http.client
import json
from typing import Iterable

from backend.utils.schema import AgenticJSOSharedState
import os
from dotenv import load_dotenv
load_dotenv()

SERP_DEV_API_KEY = os.getenv("SERP_DEV_API_KEY")
logger = logging.getLogger("agentic_jso_api")


def _extract_result_items(response: dict) -> list[dict]:
    # Serper commonly returns search results under `organic` with `link` fields.
    candidate_keys = ("results", "organic", "jobs", "news", "videos")
    items: list[dict] = []

    for key in candidate_keys:
        value = response.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    normalized = dict(item)
                    if "url" not in normalized and isinstance(normalized.get("link"), str):
                        normalized["url"] = normalized["link"]
                    items.append(normalized)

    return items


def search_query(query: str) -> list[dict]:
    conn = http.client.HTTPSConnection("google.serper.dev")
    try:
        if not SERP_DEV_API_KEY:
            logger.error("SERP_DEV_API_KEY is not configured")
            return []

        payload = json.dumps({
        "q": query
        })
        headers = {
        'X-API-KEY': SERP_DEV_API_KEY,
        'Content-Type': 'application/json'
        }
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response = json.loads(data.decode("utf-8"))

        if res.status >= 400:
            logger.error("search provider error: status=%s body=%s", res.status, response)
            return []

        items = _extract_result_items(response)
        if not items:
            logger.warning("search returned no parsable items; keys=%s", list(response.keys()))
        return items
    except Exception as exc:
        logger.error("search error: %s | query: %s", exc, query[:120])
        return []
    finally:
        conn.close()


def _normalize_queries(xray_queries: dict[str, object]) -> list[str]:
    all_queries: list[str] = []
    for source, value in xray_queries.items():
        if isinstance(value, str):
            query = value.strip()
            if query:
                all_queries.append(query)
            continue

        if isinstance(value, Iterable):
            for q in value:
                if isinstance(q, str):
                    query = q.strip()
                    if query:
                        all_queries.append(query)
            continue

        logger.warning("Ignoring invalid query payload from %s: %r", source, value)

    return all_queries


def run_parallel_search(state: AgenticJSOSharedState) -> AgenticJSOSharedState:

    xray_queries = state.xray_queries
    all_queries = _normalize_queries(xray_queries)
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(search_query, q) for q in all_queries]
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
        len(all_queries),
    )

    return state