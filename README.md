
## Overview
Build a full-stack Python application that analyzes job descriptions against resumes using Gemini AI, provides semantic matching with explainable scoring, identifies skill gaps, optimizes resumes for ATS, and conducts voice-based adaptive interviews.

## User Preferences
- **API Key:** .env file with python-dotenv
- **STT:** SpeechRecognition
- **TTS:** pyttsx3
- **Gemini Model:** gemini-2.0-flash

## Project Structure
```
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
```

## Implementation Order (22 files total)

### Step 1: Foundation
| # | File | Purpose |
|---|------|---------|
| 1 | `requirements.txt` | All Python dependencies |
| 2 | `.env` | API key placeholder |
| 3 | `.gitignore` | Exclude .env, __pycache__, .db files |
| 4 | `config.py` | Load env vars, define model names, DB path, scoring weights |

### Step 2: Database Layer
| # | File | Purpose |
|---|------|---------|
| 5 | `database/__init__.py` | Package init |
| 6 | `database/db.py` | SQLite: 5 tables (jobs, resumes, match_results, gap_analyses, interview_sessions), CRUD ops, embedding serialize/deserialize |

**Tables:**
- `jobs`: id, raw_text, structured_data (JSON), embedding (BLOB), created_at
- `resumes`: id, filename, raw_text, structured_data (JSON), embedding (BLOB), created_at
- `match_results`: id, job_id (FK), resume_id (FK), match_score, semantic_similarity, result_data (JSON), explanation, created_at
- `gap_analyses`: id, match_id (FK), gap_data (JSON), created_at
- `interview_sessions`: id, match_id (FK), questions_answers (JSON), overall_score, created_at

### Step 3: Job Processing Module
| # | File | Purpose |
|---|------|---------|
| 7 | `job_module/__init__.py` | Package init |
| 8 | `job_module/job_extractor.py` | Gemini API call with JSON mode, Pydantic JobData model, store in DB |
| 9 | `job_module/job_embedding.py` | SentenceTransformer (all-MiniLM-L6-v2) embedding generation |

**JobData Pydantic model fields:** job_title, company_name, location, experience_required, skills_required[], education_required, tools_required[], soft_skills[], job_type, salary

### Step 4: Resume Processing Module
| # | File | Purpose |
|---|------|---------|
| 10 | `resume_module/__init__.py` | Package init |
| 11 | `resume_module/resume_parser.py` | PyMuPDF text extraction + Gemini structuring + Pydantic validation |
| 12 | `resume_module/resume_embedding.py` | SentenceTransformer embedding for resume text |

**ResumeData Pydantic model fields:** skills[], projects[], experience_years, education, certifications[], tools[]

### Step 5: Match Engine
| # | File | Purpose |
|---|------|---------|
| 13 | `match_engine/__init__.py` | Package init |
| 14 | `match_engine/scorer.py` | Cosine similarity + weighted scoring (semantic 40%, skill 30%, experience 15%, education 10%, tools 5%) |
| 15 | `match_engine/explainable_ai.py` | Gemini-generated human-readable match explanation |

### Step 6: Gap Analysis + Resume Optimizer
| # | File | Purpose |
|---|------|---------|
| 16 | `gap_module/__init__.py` | Package init |
| 17 | `gap_module/skill_gap.py` | Gemini: recommended_courses[], project_suggestions[], skills_to_add[] |
| 18 | `resume_builder/__init__.py` | Package init |
| 19 | `resume_builder/optimizer.py` | Gemini ATS optimization: new_summary, project_bullets, keywords |

### Step 7: Interview Module
| # | File | Purpose |
|---|------|---------|
| 20 | `interview_module/__init__.py` | Package init |
| 21 | `interview_module/question_generator.py` | Gemini adaptive questions based on job + resume |
| 22 | `interview_module/voice_engine.py` | pyttsx3 TTS + SpeechRecognition STT with text fallback |
| 23 | `interview_module/answer_evaluator.py` | Embedding similarity + Gemini scoring (0-10 scales) |

### Step 8: Streamlit Frontend
| # | File | Purpose |
|---|------|---------|
| 24 | `app.py` | Full Streamlit UI with sidebar navigation, step-wise flow, session state |

**UI Pages:**
1. Job Description input + extraction display
2. Resume PDF upload + parsed data display
3. Match score gauge (0-100, color-coded) + breakdown + explanation
4. Skill gap analysis with course/project recommendations
5. Resume optimization suggestions with copy buttons
6. Voice interview with real-time Q&A and scoring

## Key Design Decisions
- **Gemini JSON mode:** Use `response_mime_type="application/json"` for all extraction calls
- **Embedding storage:** `numpy.tobytes()` / `numpy.frombuffer()` for SQLite BLOB storage
- **Model caching:** Singleton pattern for SentenceTransformer model (loaded once)
- **Streamlit caching:** `@st.cache_resource` for models, `@st.cache_data` for DB reads
- **Error handling:** Retry logic with exponential backoff for Gemini API calls
- **Voice fallback:** Text input box when microphone unavailable

## Dependencies (requirements.txt)
```
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
```

## Verification Strategy
1. After creating database/db.py - run a quick test to verify tables are created
2. After each module - test with sample data via Python import
3. After app.py - run `streamlit run app.py` and test the full workflow:
   - Paste a sample job description -> verify extraction
   - Upload a sample PDF resume -> verify parsing
   - Check match score display and explanation
   - Review gap analysis and optimization suggestions
   - Test interview flow (text mode at minimum)
