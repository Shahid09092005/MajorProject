import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def generate_job_embedding(job_data: dict, raw_text: str = "") -> np.ndarray:
    """Generate a semantic embedding for a job description.

    Combines key structured fields with raw text for a richer representation.
    """
    parts = []
    if job_data.get("job_title"):
        parts.append(job_data["job_title"])
    if job_data.get("skills_required"):
        parts.append(" ".join(job_data["skills_required"]))
    if job_data.get("tools_required"):
        parts.append(" ".join(job_data["tools_required"]))
    if job_data.get("education_required"):
        parts.append(job_data["education_required"])
    if raw_text:
        parts.append(raw_text[:500])

    text = " | ".join(parts) if parts else raw_text[:1000]
    model = _get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.astype(np.float32)
