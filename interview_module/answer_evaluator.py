import json
import time

import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel

from config import GEMINI_API_KEY, GEMINI_MODEL, EMBEDDING_MODEL, MAX_RETRIES, RETRY_DELAY

_model = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


class AnswerEvaluation(BaseModel):
    question: str = ""
    candidate_answer: str = ""
    answer_score: float = 0.0
    technical_depth: float = 0.0
    clarity: float = 0.0
    feedback: str = ""


EVAL_PROMPT = """You are a senior technical interviewer evaluating a candidate's answer.

Question: {question}
Category: {category}
Expected Topics: {expected_topics}

Candidate's Answer: {answer}

Evaluate the answer and return ONLY a valid JSON object with:
- "answer_score": float 0-10 (overall quality)
- "technical_depth": float 0-10 (depth of technical knowledge shown)
- "clarity": float 0-10 (how clearly the answer was communicated)
- "feedback": string (2-3 sentences of constructive feedback)

Be fair but rigorous. A score of 5 means adequate, 7+ means good, 9+ means exceptional.
"""


def evaluate_answer(question_data: dict, candidate_answer: str) -> AnswerEvaluation:
    """Evaluate a candidate's answer using embedding similarity and Gemini reasoning."""
    # Embedding-based similarity check
    model = _get_model()
    expected_text = " ".join(question_data.get("expected_topics", []))
    if expected_text and candidate_answer:
        expected_emb = model.encode(expected_text, convert_to_numpy=True).reshape(1, -1)
        answer_emb = model.encode(candidate_answer, convert_to_numpy=True).reshape(1, -1)
        similarity = float(cosine_similarity(expected_emb, answer_emb)[0][0])
    else:
        similarity = 0.0

    # Gemini-based evaluation
    genai.configure(api_key=GEMINI_API_KEY)
    llm = genai.GenerativeModel(GEMINI_MODEL)

    prompt = EVAL_PROMPT.format(
        question=question_data.get("question", ""),
        category=question_data.get("category", ""),
        expected_topics=", ".join(question_data.get("expected_topics", [])),
        answer=candidate_answer,
    )

    for attempt in range(MAX_RETRIES):
        try:
            response = llm.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text)

            # Blend LLM scores with embedding similarity (80% LLM, 20% embedding)
            llm_score = data.get("answer_score", 0)
            blended_score = round(0.8 * llm_score + 0.2 * (similarity * 10), 1)

            return AnswerEvaluation(
                question=question_data.get("question", ""),
                candidate_answer=candidate_answer,
                answer_score=blended_score,
                technical_depth=data.get("technical_depth", 0),
                clarity=data.get("clarity", 0),
                feedback=data.get("feedback", ""),
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str:
                return AnswerEvaluation(
                    question=question_data.get("question", ""),
                    candidate_answer=candidate_answer,
                    answer_score=round(similarity * 10, 1),
                    technical_depth=0,
                    clarity=0,
                    feedback="Gemini API quota exceeded. Score based on topic similarity only. "
                             "Please wait for quota to reset or enable billing.",
                )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return AnswerEvaluation(
                    question=question_data.get("question", ""),
                    candidate_answer=candidate_answer,
                    answer_score=round(similarity * 10, 1),
                    technical_depth=0,
                    clarity=0,
                    feedback=f"LLM evaluation failed: {e}. Score based on topic similarity only.",
                )
