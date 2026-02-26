# Job Application Analysis System

## Overview
This is a full-stack Python application that analyzes job descriptions against resumes using Gemini AI.  
It provides semantic matching with explainable scoring, identifies skill gaps, optimizes resumes for ATS, and conducts voice-based adaptive interviews.

---

## User Preferences
- **API Key:** Stored in `.env` file using `python-dotenv`  
- **STT (Speech-to-Text):** `SpeechRecognition`  
- **TTS (Text-to-Speech):** `pyttsx3`  
- **Gemini Model:** `gemini-2.0-flash`  

---

## Project Structure
d:\JobProject/
├── app.py                          # Streamlit frontend
├── config.py                       # Centralized configuration
├── .env                            # GEMINI_API_KEY (gitignored)
├── .gitignore
├── requirements.txt
├── database/
│   ├── __init__.py
│   └── db.py                       # SQLite CRUD + embedding serialization
├── job_module/
│   ├── __init__.py
│   ├── job_extractor.py            # Gemini extraction + Pydantic validation
│   └── job_embedding.py            # SentenceTransformer embeddings
├── resume_module/
│   ├── __init__.py
│   ├── resume_parser.py            # PyMuPDF PDF extraction + Gemini structuring
│   └── resume_embedding.py         # SentenceTransformer embeddings
├── match_engine/
│   ├── __init__.py
│   ├── scorer.py                   # Weighted multi-dimensional scoring
│   └── explainable_ai.py           # Gemini-generated explanations
├── gap_module/
│   ├── __init__.py
│   └── skill_gap.py                # Gemini gap analysis + recommendations
├── resume_builder/
│   ├── __init__.py
│   └── optimizer.py                # Gemini ATS optimization
└── interview_module/
    ├── __init__.py
    ├── question_generator.py       # Gemini adaptive question generation
    ├── voice_engine.py             # pyttsx3 TTS + SpeechRecognition STT
    └── answer_evaluator.py         # Embedding similarity + Gemini evaluation


---

## Implementation Steps

### Step 1: Foundation
- `requirements.txt`: All Python dependencies  
- `.env`: API key placeholder  
- `.gitignore`: Exclude `.env`, `__pycache__`, `.db` files  
- `config.py`: Load env vars, model names, DB path, scoring weights  

### Step 2: Database Layer
- `database/db.py`: SQLite tables for jobs, resumes, match results, gap analyses, and interview sessions  
- CRUD operations and embedding serialization  

### Step 3: Job Processing Module
- `job_module/job_extractor.py`: Gemini API extraction + Pydantic validation  
- `job_module/job_embedding.py`: SentenceTransformer embeddings  

### Step 4: Resume Processing Module
- `resume_module/resume_parser.py`: PDF extraction + Gemini structuring  
- `resume_module/resume_embedding.py`: Embedding generation  

### Step 5: Match Engine
- `match_engine/scorer.py`: Cosine similarity + weighted scoring  
- `match_engine/explainable_ai.py`: Gemini-generated explanations  

### Step 6: Gap Analysis + Resume Optimizer
- `gap_module/skill_gap.py`: Skill gap analysis + recommendations  
- `resume_builder/optimizer.py`: ATS optimization suggestions  

### Step 7: Interview Module
- `interview_module/question_generator.py`: Adaptive question generation  
- `interview_module/voice_engine.py`: TTS + STT  
- `interview_module/answer_evaluator.py`: Scoring and evaluation  

### Step 8: Streamlit Frontend
- `app.py`: Full Streamlit UI with sidebar navigation and step-wise workflow  

---

## Key Design Decisions
- **Gemini JSON mode:** `response_mime_type="application/json"`  
- **Embedding storage:** `numpy.tobytes()` / `numpy.frombuffer()` in SQLite BLOBs  
- **Model caching:** Singleton pattern for SentenceTransformer  
- **Streamlit caching:** `@st.cache_resource` for models, `@st.cache_data` for DB reads  
- **Error handling:** Retry logic with exponential backoff for API calls  
- **Voice fallback:** Text input when microphone unavailable  

---

## Dependencies (`requirements.txt`)
streamlit
google-generativeai
sentence-transformers
PyMuPDF
pydantic
python-dotenv
pyttsx3
SpeechRecognition
PyAudio
numpy
scikit-learn


---

## Verification Strategy
1. Test database creation after `db.py` setup  
2. Test each module with sample data via Python import  
3. Run `streamlit run app.py` and test full workflow:  
   - Paste sample job description → verify extraction  
   - Upload sample PDF resume → verify parsing  
   - Check match score and explanation  
   - Review skill gap analysis and optimization suggestions  
   - Test voice/text interview flow  

---

## Author
Shahid Mansuri
