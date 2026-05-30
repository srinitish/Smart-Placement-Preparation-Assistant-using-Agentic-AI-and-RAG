import streamlit as st

from graph import resume_analyzer_graph

from aws_s3 import (
    upload_resume_to_s3,
    download_resume_from_s3,
    list_resumes_from_s3,
    delete_resume_from_s3
)

from aws_dynamodb import (
    save_analysis_history,
    get_analysis_history,
    delete_analysis_history
)


st.set_page_config(
    page_title="Smart Placement Preparation Assistant",
    page_icon="🎯",
    layout="centered"
)

st.title("Smart Placement Preparation Assistant")
st.caption("Using Agentic AI and RAG")


if "selected_resume_name" not in st.session_state:
    st.session_state.selected_resume_name = None

if "selected_s3_key" not in st.session_state:
    st.session_state.selected_s3_key = None


# ---------------- SIDEBAR: ANALYSIS HISTORY ----------------

st.sidebar.title("Previous Analysis")

history_items = get_analysis_history()

if len(history_items) == 0:
    st.sidebar.info("No analysis history found.")
else:
    selected_history = st.sidebar.selectbox(
        "Select Previous Analysis",
        history_items,
        format_func=lambda item: f"{item['resume_name']} | {item['created_at']}"
    )

    if selected_history:
        if st.sidebar.button("Use This Resume"):
            st.session_state.selected_resume_name = selected_history["resume_name"]
            st.session_state.selected_s3_key = selected_history["s3_key"]
            st.success(f"Selected resume: {selected_history['resume_name']}")

        if st.sidebar.button("View Saved Result"):
            st.subheader("Previous Placement Readiness Result")

            st.write("Resume:", selected_history["resume_name"])

            st.subheader("Matched Skills")
            if selected_history["matched_skills"]:
                st.success(", ".join(selected_history["matched_skills"]))
            else:
                st.warning("No matched skills found.")

            st.subheader("Missing Skills")
            if selected_history["missing_skills"]:
                st.error(", ".join(selected_history["missing_skills"]))
            else:
                st.success("No missing skills found.")

            st.subheader("Placement Readiness Score")
            st.metric(
                "Readiness Score",
                f"{selected_history['match_score']}%"
            )

            st.subheader("Preparation Advice")
            st.write(selected_history["advice"])

        if st.sidebar.button("Delete Saved History"):
            deleted = delete_analysis_history(selected_history["resume_id"])

            if deleted:
                st.success("History deleted successfully.")
                st.rerun()
            else:
                st.error("Failed to delete history.")


# ---------------- SIDEBAR: S3 RESUME FILES ----------------

st.sidebar.divider()
st.sidebar.title("Resume Files")

resumes = list_resumes_from_s3()

if len(resumes) == 0:
    st.sidebar.info("No resumes found in S3.")
else:
    selected_resume = st.sidebar.selectbox(
        "Select Resume from Cloud",
        resumes,
        format_func=lambda resume: resume["name"]
    )

    if selected_resume:
        if st.sidebar.button("Use Selected Resume"):
            st.session_state.selected_resume_name = selected_resume["name"]
            st.session_state.selected_s3_key = selected_resume["key"]
            st.success(f"Selected resume: {selected_resume['name']}")

        if st.sidebar.button("Delete Selected Resume"):
            deleted = delete_resume_from_s3(selected_resume["key"])

            if deleted:
                st.success(f"Deleted resume: {selected_resume['name']}")

                if st.session_state.selected_s3_key == selected_resume["key"]:
                    st.session_state.selected_resume_name = None
                    st.session_state.selected_s3_key = None

                st.rerun()
            else:
                st.error("Failed to delete resume from S3.")


# ---------------- MAIN UI ----------------

st.subheader("Analyze Your Placement Readiness")

uploaded_file = st.file_uploader(
    "Upload your resume PDF",
    type=["pdf"]
)

if st.session_state.selected_resume_name:
    st.info(
        f"Using selected resume: {st.session_state.selected_resume_name}"
    )

job_description = st.text_area(
    "Paste the company job description",
    height=250,
    placeholder="Paste the job description from the company here..."
)

analyze_button = st.button("Check Placement Readiness")


# ---------------- ANALYSIS LOGIC ----------------

if analyze_button:

    if uploaded_file is None and st.session_state.selected_s3_key is None:
        st.warning("Please upload a resume or select one from cloud history.")

    elif job_description.strip() == "":
        st.warning("Please paste the company job description.")

    else:
        with st.spinner("Analyzing your resume and preparing your placement roadmap..."):

            if uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()

                s3_file_path = upload_resume_to_s3(
                    file_bytes,
                    uploaded_file.name
                )

                if s3_file_path is None:
                    st.error("Failed to upload resume to cloud storage.")
                    st.stop()

                resume_name = uploaded_file.name

            else:
                s3_file_path = st.session_state.selected_s3_key
                resume_name = st.session_state.selected_resume_name

            resume_file_for_analysis = download_resume_from_s3(s3_file_path)

            if resume_file_for_analysis is None:
                st.error("Failed to load resume from cloud storage.")
                st.stop()

            result = resume_analyzer_graph.invoke({
                "uploaded_file": resume_file_for_analysis,
                "job_description": job_description,

                "resume_text": "",
                "resume_chunks": [],
                "vectorstore": None,

                "jd_skills": [],
                "matched_skills": [],
                "missing_skills": [],
                "match_score": 0,
                "evidence": {},

                "advice": ""
            })

            save_analysis_history(
                resume_name=resume_name,
                s3_key=s3_file_path,
                job_description=job_description,
                matched_skills=result["matched_skills"],
                missing_skills=result["missing_skills"],
                match_score=result["match_score"],
                advice=result["advice"]
            )

        st.success("Placement readiness analysis completed!")

        st.subheader("Matched Skills")
        if result["matched_skills"]:
            st.success(", ".join(result["matched_skills"]))
        else:
            st.warning("No matched skills found.")

        st.subheader("Skills to Improve")
        if result["missing_skills"]:
            st.error(", ".join(result["missing_skills"]))
        else:
            st.success("Your resume matches the job description well.")

        st.subheader("Placement Readiness Score")
        st.metric(
            "Readiness Score",
            f"{result['match_score']}%"
        )

        st.subheader("Personalized Preparation Roadmap")
        st.write(result["advice"])