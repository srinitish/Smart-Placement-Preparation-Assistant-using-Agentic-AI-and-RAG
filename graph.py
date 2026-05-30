from typing import TypedDict, List, Any, Dict

from langgraph.graph import StateGraph, END

from rag_pipeline import process_resume
from agents import (
    jd_skill_extraction_agent,
    resume_skill_matching_agent,
    skill_improvement_advisor_agent
)


class ResumeAnalyzerState(TypedDict):
    uploaded_file: Any
    job_description: str

    resume_text: str
    resume_chunks: List[str]
    vectorstore: Any

    jd_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    match_score: float
    evidence: Dict

    advice: str


def resume_processing_node(state: ResumeAnalyzerState):
    resume_text, resume_chunks, vectorstore = process_resume(
        state["uploaded_file"]
    )

    state["resume_text"] = resume_text
    state["resume_chunks"] = resume_chunks
    state["vectorstore"] = vectorstore

    return state


def jd_skill_extraction_node(state: ResumeAnalyzerState):
    jd_skills = jd_skill_extraction_agent(
        state["job_description"]
    )

    state["jd_skills"] = jd_skills
    return state


def resume_skill_matching_node(state: ResumeAnalyzerState):
    matched_skills, missing_skills, match_score, evidence = resume_skill_matching_agent(
        state["vectorstore"],
        state["jd_skills"],
        state["resume_text"]
    )

    state["matched_skills"] = matched_skills
    state["missing_skills"] = missing_skills
    state["match_score"] = match_score
    state["evidence"] = evidence

    return state


def skill_advice_node(state: ResumeAnalyzerState):
    advice = skill_improvement_advisor_agent(
        state["job_description"],
        state["jd_skills"],
        state["matched_skills"],
        state["missing_skills"]
    )

    state["advice"] = advice
    return state


def build_resume_analyzer_graph():
    graph = StateGraph(ResumeAnalyzerState)

    graph.add_node("resume_processing", resume_processing_node)
    graph.add_node("jd_skill_extraction", jd_skill_extraction_node)
    graph.add_node("resume_skill_matching", resume_skill_matching_node)
    graph.add_node("skill_advice", skill_advice_node)

    graph.set_entry_point("resume_processing")

    graph.add_edge("resume_processing", "jd_skill_extraction")
    graph.add_edge("jd_skill_extraction", "resume_skill_matching")
    graph.add_edge("resume_skill_matching", "skill_advice")
    graph.add_edge("skill_advice", END)

    return graph.compile()


resume_analyzer_graph = build_resume_analyzer_graph()
