import json
import time
from typing import List, Optional

import fitz  # PyMuPDF
import google.generativeai as genai
from pydantic import BaseModel, Field

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_RETRIES, RETRY_DELAY
from database import db


class ResumeData(BaseModel):
    skills: List[str] = Field(default_factory=list)
    projects: List[dict] = Field(default_factory=list)
    experience_years: str = ""
    education: str = ""
    certifications: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


PARSING_PROMPT = """Extract structured information from the following resume text.
Return ONLY a valid JSON object with these exact keys:
- "skills": list of strings (technical skills)
- "projects": list of objects, each with "title", "description", "technologies" keys
- "experience_years": string (e.g. "3", "5+", "1-2")
- "education": string (highest degree and field)
- "certifications": list of strings
- "tools": list of strings (software tools, frameworks, platforms)

Normalize all skill and tool names to lowercase.
If a field is not found, use an empty string or empty list.

Resume Text:
{resume_text}
"""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes using PyMuPDF."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts).strip()


def parse_resume(raw_text: str) -> ResumeData:
    """Send resume text to Gemini for structured extraction."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    prompt = PARSING_PROMPT.format(resume_text=raw_text)

    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text)
            resume_data = ResumeData(**data)
            return resume_data
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
                raise RuntimeError(f"Failed to parse resume after {MAX_RETRIES} attempts: {e}")


def process_resume(filename: str, file_bytes: bytes, embedding=None) -> tuple[int, ResumeData, str]:
    """Extract, parse, and store a resume. Returns (resume_id, ResumeData, raw_text)."""
    raw_text = extract_text_from_pdf(file_bytes)
    resume_data = parse_resume(raw_text)
    resume_id = db.save_resume(filename, raw_text, resume_data.model_dump(), embedding)
    return resume_id, resume_data, raw_text
