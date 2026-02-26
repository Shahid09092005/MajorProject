import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "jobs.db")

SCORING_WEIGHTS = {
    "semantic": 0.40,
    "skill": 0.30,
    "experience": 0.15,
    "education": 0.10,
    "tools": 0.05,
}

MAX_RETRIES = 3
RETRY_DELAY = 2
DEFAULT_NUM_QUESTIONS = 5
