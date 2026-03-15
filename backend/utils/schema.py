from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AgenticJSOSharedState(BaseModel):
    query: str
    job_search_intent: Optional[List[str]]
    resume_path: str
    resume_data: dict
    target_roles: list[str]
    location_preferences: Optional[List[str]]
    skills: list[str]
    expanded_titles: list[str]
    domain: Optional[List[str]]
    xray_queries: Dict[str, str]
    search_results: List[dict]

class HealthResponse(BaseModel):
	status: str


class SearchResponse(BaseModel):
	search_results: list[dict[str, Any]]