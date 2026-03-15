from backend.utils.schema import AgenticJSOSharedState
from backend.utils.prompts import QueryExpansionPrompt
from backend.utils.config import GEMINI_MODEL
from deepagents import create_deep_agent
import json
import logging
from typing import Any

agent = create_deep_agent(model=GEMINI_MODEL,
                          system_prompt=QueryExpansionPrompt,
                          )

logger = logging.getLogger("agentic_jso_api")


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
                parts = []
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
        parts = []
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
        raise ValueError("query expansion returned an empty response")

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
            f"query expansion produced non-JSON output: {snippet!r}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError("query expansion output must be a JSON object")

    return parsed


def _coerce_to_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _fallback_expansion(state: AgenticJSOSharedState) -> dict[str, list[str]]:
    query = (state.query or "").strip()
    resume_skills = _coerce_to_string_list((state.resume_data or {}).get("skills", []))

    target_roles = [query] if query else []
    expanded_titles = [query] if query else []

    # Keep fallback compact and deterministic so downstream query generation still works.
    return {
        "target_roles": target_roles,
        "skills": resume_skills[:20],
        "expanded_titles": expanded_titles,
        "domain": [],
    }


def _invoke_query_expansion(task: str) -> dict[str, Any]:
    response = agent.invoke({"messages": [{"role": "user", "content": task}]})
    raw_content = _extract_text_from_agent_response(response)
    return _extract_json_payload(raw_content)

def query_expansion(state: AgenticJSOSharedState) -> AgenticJSOSharedState:
    task = f"Expand the following job search query: '{state.query}' with intent: {state.job_search_intent} and resume data: {state.resume_data}"
    parsed: dict[str, Any] | None = None

    try:
        parsed = _invoke_query_expansion(task)
    except ValueError as first_exc:
        retry_task = (
            f"{task}\n\n"
            "You must return a valid JSON object only, with keys: "
            "target_roles, skills, expanded_titles, domain."
        )
        try:
            parsed = _invoke_query_expansion(retry_task)
            logger.warning("Query expansion required one retry due to invalid/empty output")
        except ValueError:
            logger.warning("Query expansion failed twice; using deterministic fallback", exc_info=first_exc)
            parsed = _fallback_expansion(state)

    state.target_roles = _coerce_to_string_list(parsed.get("target_roles", []))
    state.skills = _coerce_to_string_list(parsed.get("skills", []))
    state.expanded_titles = _coerce_to_string_list(parsed.get("expanded_titles", []))
    state.domain = _coerce_to_string_list(parsed.get("domain", []))

    return state