import json
import time
from typing import List

import google.generativeai as genai
from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_DELAY


class GapAnalysis(BaseModel):
    recommended_courses: List[dict] = Field(default_factory=list)
    project_suggestions: List[dict] = Field(default_factory=list)
    skills_to_add: List[str] = Field(default_factory=list)


GAP_PROMPT = """You are an expert career advisor. A candidate is applying for a job but has skill gaps.
Analyze the gaps and provide actionable recommendations.

Missing Skills: {missing_skills}
Missing Tools: {missing_tools}

Job Details:
- Title: {job_title}
- Required Skills: {required_skills}
- Required Tools: {required_tools}

Candidate Profile:
- Current Skills: {candidate_skills}
- Current Tools: {candidate_tools}
- Experience: {experience}
- Education: {education}

Return ONLY a valid JSON object with these keys:
- "recommended_courses": list of objects with "name", "platform", "skill_covered" keys
- "project_suggestions": list of objects with "title", "description", "skills_practiced" keys
- "skills_to_add": list of strings (prioritized skills the candidate should learn first)

Provide at least 3 courses and 2 project suggestions. Prioritize skills by relevance to the job.
"""


def analyze_skill_gap(job_data: dict, resume_data: dict, match_result_data: dict) -> GapAnalysis:
    """Use Gemini to analyze skill gaps and recommend learning resources."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = GAP_PROMPT.format(
        missing_skills=", ".join(match_result_data.get("missing_skills", [])) or "None",
        missing_tools=", ".join(match_result_data.get("missing_tools", [])) or "None",
        job_title=job_data.get("job_title", "N/A"),
        required_skills=", ".join(job_data.get("skills_required", [])),
        required_tools=", ".join(job_data.get("tools_required", [])),
        candidate_skills=", ".join(resume_data.get("skills", [])),
        candidate_tools=", ".join(resume_data.get("tools", [])),
        experience=resume_data.get("experience_years", "N/A"),
        education=resume_data.get("education", "N/A"),
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text)
            return GapAnalysis(**data)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str:
                raise RuntimeError(
                    "Gemini API quota exceeded. Your free-tier limit has been reached. "
                    "Please wait for it to reset or enable billing at "
                    "https://ai.google.dev/gemini-api/docs/rate-limits"
                )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise RuntimeError(f"Failed to analyze skill gap after {MAX_RETRIES} attempts: {e}")
