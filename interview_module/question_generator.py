import json
import time
from typing import List

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_DELAY


QUESTION_PROMPT = """You are a senior technical interviewer. Generate interview questions
for a candidate applying to the following role.

Job Title: {job_title}
Required Skills: {required_skills}
Required Tools: {required_tools}

Candidate Profile:
- Skills: {candidate_skills}
- Experience: {experience}
- Education: {education}

Match Score: {match_score}/100
Missing Skills: {missing_skills}

Generate {num_questions} interview questions. Include a mix of:
- Technical questions (test claimed skills depth)
- Behavioral questions (soft skills and teamwork)
- Scenario-based questions (problem solving)

Return ONLY a valid JSON array where each element has:
- "question": string
- "category": string ("technical", "behavioral", or "scenario")
- "difficulty": string ("easy", "medium", "hard")
- "expected_topics": list of strings (key topics a good answer should cover)

Order questions from easy to hard.
"""


def generate_questions(job_data: dict, resume_data: dict,
                       match_score: float, missing_skills: list,
                       num_questions: int = 5) -> List[dict]:
    """Generate adaptive interview questions using Gemini."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = QUESTION_PROMPT.format(
        job_title=job_data.get("job_title", "N/A"),
        required_skills=", ".join(job_data.get("skills_required", [])),
        required_tools=", ".join(job_data.get("tools_required", [])),
        candidate_skills=", ".join(resume_data.get("skills", [])),
        experience=resume_data.get("experience_years", "N/A"),
        education=resume_data.get("education", "N/A"),
        match_score=match_score,
        missing_skills=", ".join(missing_skills) or "None",
        num_questions=num_questions,
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            questions = json.loads(response.text)
            if isinstance(questions, list):
                return questions
            raise ValueError("Expected a JSON array of questions")
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
                raise RuntimeError(f"Failed to generate questions after {MAX_RETRIES} attempts: {e}")
