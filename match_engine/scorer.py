import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import SCORING_WEIGHTS
from database import db


def compute_semantic_similarity(job_embedding: np.ndarray, resume_embedding: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings. Returns 0-1."""
    sim = cosine_similarity(
        job_embedding.reshape(1, -1),
        resume_embedding.reshape(1, -1),
    )[0][0]
    return float(max(0.0, min(1.0, sim)))


def compute_skill_match(job_skills: list[str], resume_skills: list[str]) -> dict:
    """Compare required skills against resume skills."""
    job_set = {s.lower().strip() for s in job_skills}
    resume_set = {s.lower().strip() for s in resume_skills}
    matched = sorted(job_set & resume_set)
    missing = sorted(job_set - resume_set)
    pct = (len(matched) / len(job_set) * 100) if job_set else 100.0
    return {"matched_skills": matched, "missing_skills": missing, "match_percentage": round(pct, 1)}


def compute_experience_match(required: str, candidate: str) -> float:
    """Heuristic experience match. Returns 0-100."""
    def _parse_years(text: str) -> float:
        text = text.lower().replace("+", "").replace("years", "").replace("year", "").strip()
        if "-" in text:
            parts = text.split("-")
            try:
                return (float(parts[0]) + float(parts[1])) / 2
            except ValueError:
                return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0

    req = _parse_years(required)
    cand = _parse_years(candidate)
    if req == 0:
        return 100.0
    ratio = cand / req if req > 0 else 1.0
    return round(min(ratio * 100, 100.0), 1)


def compute_education_match(required_edu: str, candidate_edu: str) -> float:
    """Simple education level matching. Returns 0-100."""
    levels = {"high school": 1, "diploma": 2, "associate": 2, "bachelor": 3, "master": 4, "phd": 5, "doctorate": 5}
    req_level = 0
    cand_level = 0
    req_lower = required_edu.lower()
    cand_lower = candidate_edu.lower()
    for keyword, level in levels.items():
        if keyword in req_lower:
            req_level = max(req_level, level)
        if keyword in cand_lower:
            cand_level = max(cand_level, level)
    if req_level == 0:
        return 100.0
    if cand_level >= req_level:
        return 100.0
    return round(cand_level / req_level * 100, 1)


def compute_tools_match(job_tools: list[str], resume_tools: list[str]) -> dict:
    """Compare required tools against resume tools."""
    job_set = {t.lower().strip() for t in job_tools}
    resume_set = {t.lower().strip() for t in resume_tools}
    matched = sorted(job_set & resume_set)
    missing = sorted(job_set - resume_set)
    pct = (len(matched) / len(job_set) * 100) if job_set else 100.0
    return {"matched_tools": matched, "missing_tools": missing, "match_percentage": round(pct, 1)}


def calculate_match_score(job_id: int, resume_id: int) -> dict:
    """Calculate weighted match score between a job and resume.

    Returns a comprehensive result dict and stores it in the database.
    """
    job = db.get_job(job_id)
    resume = db.get_resume(resume_id)
    if not job or not resume:
        raise ValueError("Job or resume not found in database.")

    job_data = job["structured_data"]
    resume_data = resume["structured_data"]

    # Semantic similarity
    sem_sim = 0.0
    if job.get("embedding") is not None and resume.get("embedding") is not None:
        sem_sim = compute_semantic_similarity(job["embedding"], resume["embedding"])

    # Skill match
    skill_result = compute_skill_match(
        job_data.get("skills_required", []),
        resume_data.get("skills", []),
    )

    # Experience match
    exp_score = compute_experience_match(
        job_data.get("experience_required", ""),
        resume_data.get("experience_years", ""),
    )

    # Education match
    edu_score = compute_education_match(
        job_data.get("education_required", ""),
        resume_data.get("education", ""),
    )

    # Tools match
    tools_result = compute_tools_match(
        job_data.get("tools_required", []),
        resume_data.get("tools", []),
    )

    # Weighted final score
    w = SCORING_WEIGHTS
    final_score = (
        w["semantic"] * (sem_sim * 100)
        + w["skill"] * skill_result["match_percentage"]
        + w["experience"] * exp_score
        + w["education"] * edu_score
        + w["tools"] * tools_result["match_percentage"]
    )
    final_score = round(min(final_score, 100.0), 1)

    result_data = {
        "matched_skills": skill_result["matched_skills"],
        "missing_skills": skill_result["missing_skills"],
        "skill_match_pct": skill_result["match_percentage"],
        "experience_score": exp_score,
        "education_score": edu_score,
        "matched_tools": tools_result["matched_tools"],
        "missing_tools": tools_result["missing_tools"],
        "tools_match_pct": tools_result["match_percentage"],
    }

    result = {
        "match_score": final_score,
        "semantic_similarity": round(sem_sim, 4),
        "result_data": result_data,
        "job_data": job_data,
        "resume_data": resume_data,
    }

    return result
