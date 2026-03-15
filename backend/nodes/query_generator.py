import json
import logging
import re
from typing import Any

from deepagents import create_deep_agent

from backend.utils.config import GEMINI_MODEL
from backend.utils.prompts import XrayQueryGenerationPrompt
from backend.utils.schema import AgenticJSOSharedState


logger = logging.getLogger("agentic_jso_api")

agent = create_deep_agent(
    model=GEMINI_MODEL,
    system_prompt=XrayQueryGenerationPrompt,
)


REQUIRED_SOURCES = {
    "linkedin": "site:linkedin.com/jobs",
    "greenhouse": "site:boards.greenhouse.io",
    "lever": "site:jobs.lever.co",
    "wellfound": "site:wellfound.com/jobs",
}

ROLE_NOISE_TOKENS = {
    "engineer",
    "developer",
    "specialist",
    "lead",
    "manager",
    "intern",
    "junior",
    "senior",
    "staff",
    "principal",
    "i",
    "ii",
    "iii",
    "iv",
}

LOW_VALUE_SKILLS = {
    "communication",
    "teamwork",
    "problem solving",
    "leadership",
    "adaptability",
    "microsoft office",
    "excel",
    "word",
    "powerpoint",
}


def _normalized_unique(values: list[str] | None) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []

    for value in values or []:
        cleaned = str(value).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(cleaned)

    return normalized


def _extract_text_from_agent_response(response: object) -> str:
    if isinstance(response, str):
        return response

    if isinstance(response, dict):
        messages = response.get("messages")
        if isinstance(messages, list) and messages:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                content = last_message.get("content", "")
            else:
                content = getattr(last_message, "content", "")

            if isinstance(content, list):
                parts: list[str] = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        parts.append(part)
                return "\n".join(parts).strip()

            if isinstance(content, str):
                return content

        output = response.get("output")
        if isinstance(output, str):
            return output

    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts).strip()

    return str(response)


def _extract_json_payload(raw_content: str) -> dict[str, Any]:
    text = (raw_content or "").strip()
    if not text:
        raise ValueError("xray query generation returned an empty response")

    if "```" in text:
        text = text.replace("```json", "```")
        fenced_parts = [part.strip() for part in text.split("```") if part.strip()]
        if fenced_parts:
            text = fenced_parts[0]

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
        text = text[first_brace:last_brace + 1]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        snippet = text[:200].replace("\n", " ")
        raise ValueError(
            f"xray query generation produced non-JSON output: {snippet!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError("xray query generation output must be a JSON object")

    return parsed


def _role_signature(role: str) -> str:
    role_tokens = re.findall(r"[a-z0-9]+", role.lower())
    filtered = [token for token in role_tokens if token not in ROLE_NOISE_TOKENS]
    return " ".join(filtered) if filtered else " ".join(role_tokens)


def _compact_roles(roles: list[str]) -> list[str]:
    grouped: dict[str, str] = {}
    for role in roles:
        signature = _role_signature(role)
        if not signature:
            continue
        existing = grouped.get(signature)
        if existing is None:
            grouped[signature] = role
            continue
        # Prefer shorter wording when two roles map to the same semantic signature.
        grouped[signature] = role if len(role) < len(existing) else existing
    return list(grouped.values())


def _prune_low_value_skills(skills: list[str]) -> list[str]:
    pruned: list[str] = []
    for skill in skills:
        if skill.lower() in LOW_VALUE_SKILLS:
            continue
        pruned.append(skill)
    return pruned


def _prepare_payload_for_prompt(state: AgenticJSOSharedState) -> dict[str, list[str]]:
    roles = _normalized_unique((state.target_roles or []) + (state.expanded_titles or []))
    skills = _normalized_unique(state.skills)
    domains = _normalized_unique(state.domain)
    location = _normalized_unique(state.location_preferences)
    intent = _normalized_unique(state.job_search_intent)

    compact_roles = _compact_roles(roles)
    compact_skills = _prune_low_value_skills(skills)

    verbose = len(compact_roles) + len(compact_skills) + len(domains) > 20
    if verbose:
        compact_roles = compact_roles[:8]
        compact_skills = compact_skills[:10]
        domains = domains[:4]

    return {
        "roles": compact_roles,
        "skills": compact_skills,
        "domains": domains,
        "location": location,
        "intent": intent,
    }


def _validate_queries_shape(parsed: dict[str, Any]) -> dict[str, str]:
    queries: dict[str, str] = {}

    missing = [source for source in REQUIRED_SOURCES if source not in parsed]
    if missing:
        raise ValueError(f"xray query generation missing keys: {missing}")

    for source, required_site_filter in REQUIRED_SOURCES.items():
        value = parsed.get(source)
        if not isinstance(value, str):
            raise ValueError(f"xray query for {source} must be a string")

        query = value.strip()
        if not query:
            raise ValueError(f"xray query for {source} must not be empty")

        if required_site_filter not in query:
            raise ValueError(
                f"xray query for {source} must include required site filter: {required_site_filter}"
            )

        queries[source] = query

    return queries


def _invoke_xray_query_generation(task: str) -> dict[str, Any]:
    response = agent.invoke({"messages": [{"role": "user", "content": task}]})
    raw_content = _extract_text_from_agent_response(response)
    return _extract_json_payload(raw_content)


def generate_job_query(state: AgenticJSOSharedState) -> AgenticJSOSharedState:
    query_payload = _prepare_payload_for_prompt(state)
    payload_json = json.dumps(query_payload, ensure_ascii=True)

    task = (
        "Generate precise xray queries for each source using this payload: "
        f"{payload_json}. "
        "Give special attention to intent and location when present. "
        "If the query would be long, combine very similar roles and remove low-value terms. "
        "Return JSON only with keys linkedin, greenhouse, lever, wellfound."
    )

    try:
        parsed = _invoke_xray_query_generation(task)
    except ValueError as first_exc:
        retry_task = (
            f"{task}\n\n"
            "Return valid JSON only. "
            "Each value must be a single query string and must include the correct site: filter."
        )
        try:
            parsed = _invoke_xray_query_generation(retry_task)
            logger.warning("Xray query generation required one retry due to invalid output")
        except ValueError as second_exc:
            raise ValueError(f"xray query generation failed: {second_exc}") from first_exc

    state.xray_queries = _validate_queries_shape(parsed)
    return state

