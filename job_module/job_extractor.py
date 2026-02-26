import json
import time
from typing import List, Optional

import google.generativeai as genai
from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_DELAY
from database import db


class JobData(BaseModel):
    job_title: str = ""
    company_name: str = ""
    location: str = ""
    experience_required: str = ""
    skills_required: List[str] = Field(default_factory=list)
    education_required: str = ""
    tools_required: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    job_type: str = ""
    salary: Optional[str] = None


EXTRACTION_PROMPT = """Extract structured information from the following job description.
Return ONLY a valid JSON object with these exact keys:
- "job_title": string
- "company_name": string
- "location": string
- "experience_required": string (e.g. "3-5 years")
- "skills_required": list of strings
- "education_required": string
- "tools_required": list of strings
- "soft_skills": list of strings
- "job_type": string (e.g. "Full-time", "Remote", "Hybrid")
- "salary": string or null

If a field is not found in the text, use an empty string or empty list as appropriate.
Normalize all skill and tool names to lowercase.

Job Description:
{job_text}
"""


def extract_job_description(raw_text: str) -> JobData:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = EXTRACTION_PROMPT.format(job_text=raw_text)

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text)
            job_data = JobData(**data)
            return job_data
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str:
                raise RuntimeError(
                    "Gemini API quota exceeded. Your free-tier limit has been reached. "
                    "Please wait for it to reset (usually daily) or enable billing at "
                    "https://ai.google.dev/gemini-api/docs/rate-limits"
                )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to extract job description after {MAX_RETRIES} attempts: {e}")


def process_job(raw_text: str, embedding=None) -> tuple[int, JobData]:
    """Extract job data and store in database. Returns (job_id, JobData)."""
    job_data = extract_job_description(raw_text)
    job_id = db.save_job(raw_text, job_data.model_dump(), embedding)
    return job_id, job_data
