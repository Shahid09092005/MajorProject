import streamlit as st
import json
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from database import db
from job_module.job_extractor import extract_job_description
from job_module.job_embedding import generate_job_embedding
from resume_module.resume_parser import extract_text_from_pdf, parse_resume
from resume_module.resume_embedding import generate_resume_embedding
from match_engine.scorer import calculate_match_score
from match_engine.explainable_ai import generate_explanation
from gap_module.skill_gap import analyze_skill_gap
from resume_builder.optimizer import optimize_resume
from interview_module.question_generator import generate_questions
from interview_module.voice_engine import speak, listen, is_microphone_available
from interview_module.answer_evaluator import evaluate_answer

# ───────── Page config ─────────
st.set_page_config(page_title="Job Application Analyzer", page_icon="💼", layout="wide")

# Initialize database
db.init_db()

# ───────── Session state defaults ─────────
_defaults = {
    "job_id": None,
    "job_data": None,
    "resume_id": None,
    "resume_data": None,
    "match_id": None,
    "match_result": None,
    "explanation": None,
    "gap_analysis": None,
    "optimization": None,
    "interview_questions": None,
    "interview_idx": 0,
    "interview_answers": [],
    "interview_done": False,
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ───────── Sidebar ─────────
st.sidebar.title("Navigation")
steps = [
    "1. Job Description",
    "2. Upload Resume",
    "3. Match Analysis",
    "4. Skill Gap",
    "5. Resume Optimizer",
    "6. Mock Interview",
]
page = st.sidebar.radio("Go to", steps)

# Status indicators
st.sidebar.markdown("---")
st.sidebar.markdown("### Progress")
st.sidebar.markdown(f"{'✅' if st.session_state.job_data else '⬜'} Job extracted")
st.sidebar.markdown(f"{'✅' if st.session_state.resume_data else '⬜'} Resume parsed")
st.sidebar.markdown(f"{'✅' if st.session_state.match_result else '⬜'} Match scored")
st.sidebar.markdown(f"{'✅' if st.session_state.gap_analysis else '⬜'} Gap analyzed")
st.sidebar.markdown(f"{'✅' if st.session_state.optimization else '⬜'} Resume optimized")
st.sidebar.markdown(f"{'✅' if st.session_state.interview_done else '⬜'} Interview done")


# ═══════════════════════════════════════════
# PAGE 1 — Job Description
# ═══════════════════════════════════════════
if page == steps[0]:
    st.header("Step 1: Job Description")
    st.write("Paste the full job description below and click **Extract**.")

    with st.form("job_form"):
        job_text = st.text_area("Job Description", height=300,
                                placeholder="Paste the full job description here...")
        submitted = st.form_submit_button("Extract Job Details")

    if submitted and job_text.strip():
        with st.spinner("Extracting job details with Gemini..."):
            try:
                job_data_obj = extract_job_description(job_text)
                job_dict = job_data_obj.model_dump()

                embedding = generate_job_embedding(job_dict, job_text)
                job_id = db.save_job(job_text, job_dict, embedding)

                st.session_state.job_id = job_id
                st.session_state.job_data = job_dict
                # Reset downstream
                st.session_state.match_id = None
                st.session_state.match_result = None
                st.session_state.explanation = None
                st.session_state.gap_analysis = None
                st.session_state.optimization = None
                st.success("Job description extracted successfully!")
            except Exception as e:
                st.error(f"Extraction failed: {e}")
    elif submitted:
        st.warning("Please paste a job description first.")

    if st.session_state.job_data:
        st.subheader("Extracted Job Data")
        jd = st.session_state.job_data
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Job Title:** {jd.get('job_title', 'N/A')}")
            st.markdown(f"**Company:** {jd.get('company_name', 'N/A')}")
            st.markdown(f"**Location:** {jd.get('location', 'N/A')}")
            st.markdown(f"**Job Type:** {jd.get('job_type', 'N/A')}")
            st.markdown(f"**Salary:** {jd.get('salary') or 'Not specified'}")
        with col2:
            st.markdown(f"**Experience:** {jd.get('experience_required', 'N/A')}")
            st.markdown(f"**Education:** {jd.get('education_required', 'N/A')}")

        st.markdown("**Required Skills:**")
        if jd.get("skills_required"):
            st.write(", ".join(jd["skills_required"]))
        st.markdown("**Required Tools:**")
        if jd.get("tools_required"):
            st.write(", ".join(jd["tools_required"]))
        st.markdown("**Soft Skills:**")
        if jd.get("soft_skills"):
            st.write(", ".join(jd["soft_skills"]))

        with st.expander("Raw JSON"):
            st.json(jd)


# ═══════════════════════════════════════════
# PAGE 2 — Upload Resume
# ═══════════════════════════════════════════
elif page == steps[1]:
    st.header("Step 2: Upload Resume")
    st.write("Upload your resume as a PDF file.")

    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

    if uploaded_file is not None:
        if st.button("Parse Resume", key="parse_resume_btn"):
            file_bytes = uploaded_file.read()
            if not file_bytes:
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
            with st.spinner("Extracting and parsing resume..."):
                try:
                    raw_text = extract_text_from_pdf(file_bytes)
                    resume_data_obj = parse_resume(raw_text)
                    resume_dict = resume_data_obj.model_dump()

                    embedding = generate_resume_embedding(resume_dict, raw_text)
                    resume_id = db.save_resume(uploaded_file.name, raw_text, resume_dict, embedding)

                    st.session_state.resume_id = resume_id
                    st.session_state.resume_data = resume_dict
                    # Reset downstream
                    st.session_state.match_id = None
                    st.session_state.match_result = None
                    st.session_state.explanation = None
                    st.session_state.gap_analysis = None
                    st.session_state.optimization = None
                    st.success("Resume parsed successfully!")
                except Exception as e:
                    st.error(f"Resume parsing failed: {e}")

    if st.session_state.resume_data:
        st.subheader("Parsed Resume Data")
        rd = st.session_state.resume_data
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Experience:** {rd.get('experience_years', 'N/A')} years")
            st.markdown(f"**Education:** {rd.get('education', 'N/A')}")
        with col2:
            st.markdown("**Certifications:**")
            if rd.get("certifications"):
                st.write(", ".join(rd["certifications"]))
            else:
                st.write("None listed")

        st.markdown("**Skills:**")
        if rd.get("skills"):
            st.write(", ".join(rd["skills"]))
        st.markdown("**Tools:**")
        if rd.get("tools"):
            st.write(", ".join(rd["tools"]))

        if rd.get("projects"):
            st.markdown("**Projects:**")
            for proj in rd["projects"]:
                title = proj.get("title", "Untitled")
                desc = proj.get("description", "")
                techs = ", ".join(proj.get("technologies", []))
                st.markdown(f"- **{title}**: {desc}")
                if techs:
                    st.caption(f"  Technologies: {techs}")

        with st.expander("Raw JSON"):
            st.json(rd)


# ═══════════════════════════════════════════
# PAGE 3 — Match Analysis
# ═══════════════════════════════════════════
elif page == steps[2]:
    st.header("Step 3: Match Analysis")

    if not st.session_state.job_data or not st.session_state.resume_data:
        st.warning("Please complete Step 1 (Job Description) and Step 2 (Upload Resume) first.")
    else:
        if st.button("Calculate Match Score"):
            with st.spinner("Computing match score..."):
                try:
                    result = calculate_match_score(st.session_state.job_id, st.session_state.resume_id)
                    st.session_state.match_result = result
                except Exception as e:
                    st.error(f"Matching failed: {e}")

            if st.session_state.match_result:
                with st.spinner("Generating explanation..."):
                    try:
                        explanation = generate_explanation(st.session_state.match_result)
                        st.session_state.explanation = explanation

                        # Save to database
                        rd = st.session_state.match_result["result_data"]
                        match_id = db.save_match_result(
                            st.session_state.job_id,
                            st.session_state.resume_id,
                            st.session_state.match_result["match_score"],
                            st.session_state.match_result["semantic_similarity"],
                            rd,
                            explanation,
                        )
                        st.session_state.match_id = match_id
                    except Exception as e:
                        st.error(f"Explanation generation failed: {e}")

        if st.session_state.match_result:
            mr = st.session_state.match_result
            rd = mr["result_data"]

            # Score gauge
            score = mr["match_score"]
            if score >= 70:
                color = "green"
                label = "Strong Match"
            elif score >= 50:
                color = "orange"
                label = "Moderate Match"
            else:
                color = "red"
                label = "Weak Match"

            st.markdown(f"## Match Score: <span style='color:{color}; font-size:2em'>{score}/100</span> ({label})",
                        unsafe_allow_html=True)

            # Breakdown
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Semantic Similarity", f"{mr['semantic_similarity']:.2%}")
            col2.metric("Skill Match", f"{rd['skill_match_pct']}%")
            col3.metric("Experience", f"{rd['experience_score']}%")
            col4.metric("Education", f"{rd['education_score']}%")

            # Skills
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Matched Skills** ✅")
                if rd["matched_skills"]:
                    for s in rd["matched_skills"]:
                        st.markdown(f"- {s}")
                else:
                    st.write("None")
            with c2:
                st.markdown("**Missing Skills** ❌")
                if rd["missing_skills"]:
                    for s in rd["missing_skills"]:
                        st.markdown(f"- {s}")
                else:
                    st.write("None")

            # Tools
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("**Matched Tools** ✅")
                if rd.get("matched_tools"):
                    for t in rd["matched_tools"]:
                        st.markdown(f"- {t}")
                else:
                    st.write("None")
            with c4:
                st.markdown("**Missing Tools** ❌")
                if rd.get("missing_tools"):
                    for t in rd["missing_tools"]:
                        st.markdown(f"- {t}")
                else:
                    st.write("None")

            # Explanation
            if st.session_state.explanation:
                st.markdown("---")
                st.subheader("AI Explanation")
                st.write(st.session_state.explanation)


# ═══════════════════════════════════════════
# PAGE 4 — Skill Gap
# ═══════════════════════════════════════════
elif page == steps[3]:
    st.header("Step 4: Skill Gap Analysis")

    if not st.session_state.match_result:
        st.warning("Please complete Step 3 (Match Analysis) first.")
    else:
        if st.button("Analyze Skill Gaps"):
            with st.spinner("Analyzing skill gaps with Gemini..."):
                try:
                    gap = analyze_skill_gap(
                        st.session_state.job_data,
                        st.session_state.resume_data,
                        st.session_state.match_result["result_data"],
                    )
                    gap_dict = gap.model_dump()
                    st.session_state.gap_analysis = gap_dict

                    if st.session_state.match_id:
                        db.save_gap_analysis(st.session_state.match_id, gap_dict)
                    st.success("Gap analysis complete!")
                except Exception as e:
                    st.error(f"Gap analysis failed: {e}")

        if st.session_state.gap_analysis:
            ga = st.session_state.gap_analysis

            # Skills to add
            st.subheader("Priority Skills to Learn")
            if ga.get("skills_to_add"):
                for i, skill in enumerate(ga["skills_to_add"], 1):
                    st.markdown(f"{i}. **{skill}**")
            else:
                st.write("No additional skills needed!")

            # Courses
            st.subheader("Recommended Courses")
            if ga.get("recommended_courses"):
                for course in ga["recommended_courses"]:
                    name = course.get("name", "Untitled")
                    platform = course.get("platform", "")
                    skill = course.get("skill_covered", "")
                    st.markdown(f"- **{name}** ({platform}) — covers: {skill}")
            else:
                st.write("No courses suggested.")

            # Projects
            st.subheader("Project Suggestions")
            if ga.get("project_suggestions"):
                for proj in ga["project_suggestions"]:
                    title = proj.get("title", "Untitled")
                    desc = proj.get("description", "")
                    skills = ", ".join(proj.get("skills_practiced", []))
                    st.markdown(f"**{title}**")
                    st.write(desc)
                    if skills:
                        st.caption(f"Skills practiced: {skills}")
                    st.markdown("")
            else:
                st.write("No projects suggested.")


# ═══════════════════════════════════════════
# PAGE 5 — Resume Optimizer
# ═══════════════════════════════════════════
elif page == steps[4]:
    st.header("Step 5: Resume Optimizer")

    if not st.session_state.match_result:
        st.warning("Please complete Step 3 (Match Analysis) first.")
    else:
        if st.button("Generate Optimization Suggestions"):
            with st.spinner("Optimizing resume with Gemini..."):
                try:
                    gap_data = st.session_state.gap_analysis or {}
                    opt = optimize_resume(
                        st.session_state.job_data,
                        st.session_state.resume_data,
                        gap_data,
                    )
                    st.session_state.optimization = opt.model_dump()
                    st.success("Optimization suggestions ready!")
                except Exception as e:
                    st.error(f"Optimization failed: {e}")

        if st.session_state.optimization:
            opt = st.session_state.optimization

            # New summary
            st.subheader("Optimized Professional Summary")
            st.info(opt.get("new_summary", ""))

            # Project bullets
            st.subheader("Suggested Project Bullet Points")
            if opt.get("suggested_project_bullets"):
                for bullet in opt["suggested_project_bullets"]:
                    st.markdown(f"- {bullet}")

            # Skills to emphasize
            st.subheader("Skills to Emphasize")
            if opt.get("skills_to_emphasize"):
                st.write(", ".join(opt["skills_to_emphasize"]))

            # ATS Keywords
            st.subheader("ATS Keywords to Add")
            if opt.get("keywords_added"):
                st.write(", ".join(opt["keywords_added"]))


# ═══════════════════════════════════════════
# PAGE 6 — Mock Interview
# ═══════════════════════════════════════════
elif page == steps[5]:
    st.header("Step 6: Mock Interview")

    if not st.session_state.match_result:
        st.warning("Please complete Step 3 (Match Analysis) first.")
    else:
        # Setup
        if not st.session_state.interview_questions:
            num_q = st.slider("Number of questions", 3, 10, 5)
            use_voice = st.checkbox("Enable voice (TTS/STT)", value=False)
            st.session_state["use_voice"] = use_voice

            if st.button("Start Interview"):
                with st.spinner("Generating interview questions..."):
                    try:
                        mr = st.session_state.match_result
                        questions = generate_questions(
                            st.session_state.job_data,
                            st.session_state.resume_data,
                            mr["match_score"],
                            mr["result_data"].get("missing_skills", []),
                            num_q,
                        )
                        st.session_state.interview_questions = questions
                        st.session_state.interview_idx = 0
                        st.session_state.interview_answers = []
                        st.session_state.interview_done = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Question generation failed: {e}")

        # Interview in progress
        elif not st.session_state.interview_done:
            questions = st.session_state.interview_questions
            idx = st.session_state.interview_idx
            total = len(questions)

            st.progress((idx) / total, text=f"Question {idx + 1} of {total}")

            q = questions[idx]
            st.subheader(f"Q{idx + 1}: {q['question']}")
            st.caption(f"Category: {q.get('category', 'N/A')} | Difficulty: {q.get('difficulty', 'N/A')}")

            # TTS
            use_voice = st.session_state.get("use_voice", False)
            if use_voice:
                if st.button("🔊 Read Question Aloud"):
                    speak(q["question"])

            # Answer input
            answer = ""
            if use_voice and is_microphone_available():
                col_v, col_t = st.columns(2)
                with col_v:
                    if st.button("🎤 Record Answer"):
                        with st.spinner("Listening..."):
                            answer = listen()
                            if answer:
                                st.session_state["current_answer"] = answer
                            else:
                                st.warning("Could not capture speech. Please type your answer.")
                with col_t:
                    answer = st.text_area("Or type your answer:", key=f"answer_{idx}",
                                          value=st.session_state.get("current_answer", ""))
            else:
                answer = st.text_area("Type your answer:", key=f"answer_{idx}")

            if st.button("Submit Answer", disabled=not answer):
                with st.spinner("Evaluating your answer..."):
                    try:
                        evaluation = evaluate_answer(q, answer)
                        eval_dict = evaluation.model_dump()
                        st.session_state.interview_answers.append(eval_dict)

                        st.markdown(f"**Score:** {eval_dict['answer_score']}/10")
                        st.markdown(f"**Technical Depth:** {eval_dict['technical_depth']}/10")
                        st.markdown(f"**Clarity:** {eval_dict['clarity']}/10")
                        st.markdown(f"**Feedback:** {eval_dict['feedback']}")

                        # Move to next or finish
                        if idx + 1 < total:
                            st.session_state.interview_idx = idx + 1
                            st.session_state.pop("current_answer", None)
                        else:
                            st.session_state.interview_done = True
                            # Save session
                            answers = st.session_state.interview_answers
                            avg_score = sum(a["answer_score"] for a in answers) / len(answers) if answers else 0
                            if st.session_state.match_id:
                                db.save_interview_session(st.session_state.match_id, answers, avg_score)
                    except Exception as e:
                        st.error(f"Evaluation failed: {e}")

            if st.button("Skip Question"):
                st.session_state.interview_answers.append({
                    "question": q["question"],
                    "candidate_answer": "(skipped)",
                    "answer_score": 0, "technical_depth": 0, "clarity": 0,
                    "feedback": "Question was skipped.",
                })
                if idx + 1 < total:
                    st.session_state.interview_idx = idx + 1
                    st.session_state.pop("current_answer", None)
                    st.rerun()
                else:
                    st.session_state.interview_done = True
                    answers = st.session_state.interview_answers
                    avg_score = sum(a["answer_score"] for a in answers) / len(answers) if answers else 0
                    if st.session_state.match_id:
                        db.save_interview_session(st.session_state.match_id, answers, avg_score)
                    st.rerun()

        # Interview results
        else:
            st.subheader("Interview Results")
            answers = st.session_state.interview_answers

            if answers:
                avg = sum(a["answer_score"] for a in answers) / len(answers)
                st.markdown(f"### Overall Score: **{avg:.1f}/10**")

                for i, ans in enumerate(answers, 1):
                    with st.expander(f"Q{i}: {ans['question']}", expanded=False):
                        st.markdown(f"**Your Answer:** {ans['candidate_answer']}")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Score", f"{ans['answer_score']}/10")
                        c2.metric("Tech Depth", f"{ans['technical_depth']}/10")
                        c3.metric("Clarity", f"{ans['clarity']}/10")
                        st.markdown(f"**Feedback:** {ans['feedback']}")

            if st.button("Restart Interview"):
                st.session_state.interview_questions = None
                st.session_state.interview_idx = 0
                st.session_state.interview_answers = []
                st.session_state.interview_done = False
                st.rerun()
