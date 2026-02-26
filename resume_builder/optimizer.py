import json
import time
from typing import List

import google.generativeai as genai
from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_DELAY


class OptimizedResume(BaseModel):
    new_summary: str = ""
    suggested_project_bullets: List[str] = Field(default_factory=list)
    skills_to_emphasize: List[str] = Field(default_factory=list)
    keywords_added: List[str] = Field(default_factory=list)


OPTIMIZER_PROMPT = """You are an expert resume writer and ATS optimization specialist.
Optimize the candidate's resume to better match the target job description.

Job Details:
- Title: {job_title}
- Required Skills: {required_skills}
- Required Tools: {required_tools}
- Experience Required: {experience_required}

Current Resume:
- Skills: {candidate_skills}
- Tools: {candidate_tools}
- Experience: {experience}
- Education: {education}
- Projects: {projects}

Gap Analysis:
- Missing Skills: {missing_skills}
- Skills to Add: {skills_to_add}

Return ONLY a valid JSON object with these keys:
- "new_summary": string (a professional summary paragraph optimized for this job, 3-4 sentences)
- "suggested_project_bullets": list of strings (action-oriented bullet points the candidate can add)
- "skills_to_emphasize": list of strings (skills to highlight prominently)
- "keywords_added": list of strings (ATS keywords from the job description to incorporate)

Focus on ATS keyword alignment while keeping the content truthful to the candidate's actual experience.
"""


def optimize_resume(job_data: dict, resume_data: dict, gap_data: dict) -> OptimizedResume:
    """Use Gemini to generate resume optimization suggestions."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    projects_str = json.dumps(resume_data.get("projects", []), indent=2)

    prompt = OPTIMIZER_PROMPT.format(
        job_title=job_data.get("job_title", "N/A"),
        required_skills=", ".join(job_data.get("skills_required", [])),
        required_tools=", ".join(job_data.get("tools_required", [])),
        experience_required=job_data.get("experience_required", "N/A"),
        candidate_skills=", ".join(resume_data.get("skills", [])),
        candidate_tools=", ".join(resume_data.get("tools", [])),
        experience=resume_data.get("experience_years", "N/A"),
        education=resume_data.get("education", "N/A"),
        projects=projects_str,
        missing_skills=", ".join(gap_data.get("skills_to_add", [])) or "None",
        skills_to_add=", ".join(gap_data.get("skills_to_add", [])) or "None",
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
            return OptimizedResume(**data)
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
                raise RuntimeError(f"Failed to optimize resume after {MAX_RETRIES} attempts: {e}")
