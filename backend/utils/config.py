import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_KEY")
GEMINI_MODEL = "google_genai:gemini-2.5-flash"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# Keep backward compatibility with GEMINI_KEY while satisfying providers that
# expect GOOGLE_API_KEY or GEMINI_API_KEY.
if GEMINI_KEY:
    os.environ.setdefault("GOOGLE_API_KEY", GEMINI_KEY)
    os.environ.setdefault("GEMINI_API_KEY", GEMINI_KEY)
