from utils.schema import AgenticJSOSharedState
from utils.config import GEMINI_MODEL
from nodes.xray_adapters import linkedin_xray, greenhouse_xray, lever_xray, wellfound_xray

def generate_job_query(state: AgenticJSOSharedState) -> AgenticJSOSharedState:

    roles = set(state.target_roles + state.expanded_titles)
    skills = state.skills
    domains = state.domain
    location = state.location_preferences

    query_payload = {
        "roles": roles,
        "skills": skills,
        "domains": domains,
        "location": location,
        "intent": state.job_search_intent,
    }
    
    def generate_xray_queries(query_payload: dict) -> dict:

        queries = {}

        queries["linkedin"] = linkedin_xray(query_payload)
        queries["greenhouse"] = greenhouse_xray(query_payload)
        queries["lever"] = lever_xray(query_payload)
        queries["wellfound"] = wellfound_xray(query_payload)

        return queries
    
    state.xray_queries = generate_xray_queries(query_payload)
    return state

