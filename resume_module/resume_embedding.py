import numpy as np
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def generate_resume_embedding(resume_data: dict, raw_text: str = "") -> np.ndarray:
    """Generate a semantic embedding for a resume.

    Combines structured fields with raw text for a richer representation.
    """
    parts = []
    if resume_data.get("skills"):
        parts.append(" ".join(resume_data["skills"]))
    if resume_data.get("tools"):
        parts.append(" ".join(resume_data["tools"]))
    if resume_data.get("education"):
        parts.append(resume_data["education"])
    if resume_data.get("certifications"):
        parts.append(" ".join(resume_data["certifications"]))
    if raw_text:
        parts.append(raw_text[:500])

    text = " | ".join(parts) if parts else raw_text[:1000]
    model = _get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.astype(np.float32)
