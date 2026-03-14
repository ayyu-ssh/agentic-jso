from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    # Allow running this file directly: `python nodes/query_expansion.py`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inputs import *
from utils.schema import AgenticJSOSharedState
from utils.prompts import QueryExpansionPrompt
from utils.config import GEMINI_MODEL
from deepagents import create_deep_agent
import json

agent = create_deep_agent(model=GEMINI_MODEL,
                          system_prompt=QueryExpansionPrompt,
                          )


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

def query_expansion(state: AgenticJSOSharedState) -> AgenticJSOSharedState:
    task = f"Expand the following job search query: '{state.query}' with intent: {state.job_search_intent} and resume data: {state.resume_data}"
    response = agent.invoke({"messages": [{"role": "user", "content": task}]})

    # Parse the response and update the state
    # Assuming the response is in the expected JSON format  

    raw_content = _extract_text_from_agent_response(response)
    if "```json" in raw_content:
        raw_content = raw_content.split("```json")[1].split("```")[0].strip()
    
    parsed = json.loads(raw_content)

    state.target_roles = parsed.get("target_roles", [])
    state.skills = parsed.get("skills", [])
    state.expanded_titles = parsed.get("expanded_titles", [])
    state.domain = parsed.get("domain", [])

    return state