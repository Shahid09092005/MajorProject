import json
import time

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_DELAY


EXPLANATION_PROMPT = """You are an expert career advisor. Given the following job-resume match analysis,
write a clear, helpful explanation for the candidate.

Match Score: {match_score}/100
Semantic Similarity: {semantic_similarity}
Matched Skills: {matched_skills}
Missing Skills: {missing_skills}
Experience Score: {experience_score}/100
Education Score: {education_score}/100
Tools Matched: {matched_tools}
Tools Missing: {missing_tools}

Job Title: {job_title}
Required Skills: {required_skills}

Candidate Skills: {candidate_skills}
Candidate Education: {candidate_education}
Candidate Experience: {candidate_experience}

Write 2-3 short paragraphs covering:
1. Overall fit assessment
2. Key strengths the candidate brings
3. Main gaps and what to improve

Be specific and actionable. Do not use markdown formatting.
"""


def generate_explanation(match_result: dict) -> str:
    """Use Gemini to generate a human-readable explanation of the match."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    rd = match_result["result_data"]
    jd = match_result.get("job_data", {})
    res = match_result.get("resume_data", {})

    prompt = EXPLANATION_PROMPT.format(
        match_score=match_result["match_score"],
        semantic_similarity=match_result["semantic_similarity"],
        matched_skills=", ".join(rd.get("matched_skills", [])) or "None",
        missing_skills=", ".join(rd.get("missing_skills", [])) or "None",
        experience_score=rd.get("experience_score", 0),
        education_score=rd.get("education_score", 0),
        matched_tools=", ".join(rd.get("matched_tools", [])) or "None",
        missing_tools=", ".join(rd.get("missing_tools", [])) or "None",
        job_title=jd.get("job_title", "N/A"),
        required_skills=", ".join(jd.get("skills_required", [])) or "N/A",
        candidate_skills=", ".join(res.get("skills", [])) or "N/A",
        candidate_education=res.get("education", "N/A"),
        candidate_experience=res.get("experience_years", "N/A"),
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str:
                return ("Unable to generate explanation: Gemini API quota exceeded. "
                        "Your free-tier limit has been reached. Please wait for it to reset "
                        "or enable billing at https://ai.google.dev/gemini-api/docs/rate-limits")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return f"Unable to generate explanation: {e}"
