import os
import ast
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)


def jd_skill_extraction_agent(job_description):
    prompt = f"""
    You are a technical skill extraction agent.

    Extract only technical skills from the following job description.

    Rules:
    - Return only a Python list.
    - Do not add explanation.
    - Include programming languages, frameworks, tools, databases, cloud services, AI/ML skills, and libraries.
    - Do not include soft skills.

    Job Description:
    {job_description}
    """

    response = llm.invoke(prompt)

    try:
        skills = ast.literal_eval(response.content)
        return skills
    except:
        return []
    
def resume_skill_matching_agent(vectorstore, jd_skills, resume_text):
    matched_skills = []
    missing_skills = []
    skill_evidence = {}

    resume_text_lower = resume_text.lower()

    for skill in jd_skills:
        skill_lower = skill.lower()

        # 1. Exact keyword match
        if skill_lower in resume_text_lower:
            matched_skills.append(skill)
            skill_evidence[skill] = {
                "match_type": "Exact Match",
                "score": 0,
                "evidence": f"{skill} found directly in resume text."
            }
            continue

        # 2. Semantic RAG match
        results = vectorstore.similarity_search_with_score(skill, k=1)

        if results:
            doc, score = results[0]

            # Adjusted threshold
            if score < 1.5:
                matched_skills.append(skill)
                skill_evidence[skill] = {
                    "match_type": "Semantic Match",
                    "score": score,
                    "evidence": doc.page_content
                }
            else:
                missing_skills.append(skill)
        else:
            missing_skills.append(skill)

    if len(jd_skills) == 0:
        match_score = 0
    else:
        match_score = round((len(matched_skills) / len(jd_skills)) * 100, 2)

    return matched_skills, missing_skills, match_score, skill_evidence


def skill_improvement_advisor_agent(
    job_description,
    jd_skills,
    matched_skills,
    missing_skills
):
    prompt = f"""
    You are a career guidance and technical interview preparation agent.

    A student wants to apply for the following job.

    Job Description:
    {job_description}

    Skills required in JD:
    {jd_skills}

    Skills already matched in resume:
    {matched_skills}

    Skills missing from resume:
    {missing_skills}

    Give a practical learning path to crack this interview.

    Rules:
    - Focus mainly on missing skills.
    - Give priority order.
    - Explain what to learn.
    - Suggest mini projects or practice tasks.
    - Give interview preparation topics.
    - Keep it clear and student-friendly.
    """

    response = llm.invoke(prompt)
    return response.content
        

