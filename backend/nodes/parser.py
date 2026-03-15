from pathlib import Path
import sys
from backend.utils.schema import AgenticJSOSharedState
from pyresparser import ResumeParser


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

def parse_resume(state: AgenticJSOSharedState) -> AgenticJSOSharedState:
    data = ResumeParser(state.resume_path).get_extracted_data()
    state.resume_data = data
    return state

