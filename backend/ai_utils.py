import os
import json
import re
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = None
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"Could not initialize OpenAI client: {e}")

SKILL_CATALOG = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "Express", "Django", "Flask",
    "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
    "HTML", "CSS", "Git", "REST API", "GraphQL", "Machine Learning", "Data Analysis", "TensorFlow",
    "PyTorch", "Java", "C#", "C++", "Agile", "Scrum", "Communication", "Problem Solving"
]
FALLBACK_SKILLS = [
    "Python", "JavaScript", "React", "Node.js", "SQL", "AWS", "Docker", "Kubernetes", "Git",
    "HTML", "CSS", "Machine Learning", "Data Analysis", "REST API", "GraphQL", "Agile"
]


def clean_json_response(result):
    if result.startswith("```json"):
        result = result[7:-3].strip()
    elif result.startswith("```"):
        result = result[3:-3].strip()
    return result


def extract_skills_from_text(text):
    if not text:
        return []
    normalized = text.lower()
    found = []
    for skill in SKILL_CATALOG:
        if skill.lower() in normalized:
            found.append(skill)
    return sorted(set(found), key=lambda x: normalized.index(x.lower()))


def estimate_ats_score(text, skills):
    if not text:
        return 5
    length_score = min(40, len(text) // 100)
    skill_score = min(40, len(skills) * 5)
    keyword_score = 20 if any(word in text.lower() for word in ["experience", "projects", "developed", "designed"]) else 0
    total = length_score + skill_score + keyword_score
    return max(10, min(100, total))


def fallback_analyze_resume(resume_text):
    skills = extract_skills_from_text(resume_text)
    missing_skills = [skill for skill in FALLBACK_SKILLS if skill not in skills][:8]
    ats_score = estimate_ats_score(resume_text, skills)
    chance_of_selection = min(100, max(10, ats_score + len(skills) * 2))
    suggestions = [
        "Add measurable achievements and results to every role description.",
        "Include key technical tools and frameworks that match the job requirements.",
        "Use consistent formatting and remove any spelling or grammar issues."
    ]
    return {
        "ats_score": ats_score,
        "skills": skills,
        "missing_skills": missing_skills,
        "suggestions": suggestions,
        "chance_of_selection": chance_of_selection
    }


def analyze_resume(resume_text):
    if not resume_text:
        return fallback_analyze_resume(resume_text)

    if client:
        prompt = f"""
        You are an expert ATS and technical recruiter. Analyze the following resume text.
        Return ONLY a JSON object (no markdown formatting, just raw JSON) with the following keys:
        - ats_score: an integer from 0 to 100 representing the overall resume quality and ATS parseability.
        - skills: a list of technical and soft skills extracted from the resume.
        - missing_skills: a list of important general tech skills missing from the resume based on standard software engineering or data roles.
        - suggestions: a list of actionable suggestions for improving the resume.
        - chance_of_selection: an integer from 0 to 100 representing general market competitiveness.

        Resume Text:
        {resume_text}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            result = clean_json_response(response.choices[0].message.content.strip())
            return json.loads(result)
        except Exception as e:
            print(f"Error in analyze_resume: {e}")
            return fallback_analyze_resume(resume_text)

    return fallback_analyze_resume(resume_text)


def fallback_match_job_description(resume_text, job_description):
    resume_skills = extract_skills_from_text(resume_text)
    job_skills = extract_skills_from_text(job_description)
    matched_skills = [skill for skill in resume_skills if skill in job_skills]
    missing_skills = [skill for skill in job_skills if skill not in resume_skills]
    match_percentage = int((len(matched_skills) / max(1, len(job_skills))) * 100) if job_skills else 0
    chance_of_selection = min(100, match_percentage + 10)
    return {
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "chance_of_selection": chance_of_selection
    }


def match_job_description(resume_text, job_description):
    if not resume_text or not job_description:
        return fallback_match_job_description(resume_text, job_description)

    if client:
        prompt = f"""
        You are an expert recruiter. Compare the candidate's resume with the job description.
        Return ONLY a JSON object (no markdown formatting) with the following keys:
        - match_percentage: integer from 0 to 100.
        - matched_skills: list of strings (skills found in both).
        - missing_skills: list of strings (skills required by job but missing in resume).
        - chance_of_selection: integer from 0 to 100 based on match.

        Job Description:
        {job_description}

        Resume Text:
        {resume_text}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            result = clean_json_response(response.choices[0].message.content.strip())
            return json.loads(result)
        except Exception as e:
            print(f"Error in match_job_description: {e}")
            return fallback_match_job_description(resume_text, job_description)

    return fallback_match_job_description(resume_text, job_description)


def generate_interview_questions(resume_text, job_description=None):
    if client:
        context = ""
        if job_description:
            context = f"Job Description:\n{job_description}\n\n"

        prompt = f"""
        Based on the following resume {"and job description" if job_description else ""}, generate 5 interview questions (a mix of technical and HR/behavioral).
        Return ONLY a JSON object (no markdown formatting) with the key \"questions\", which is a list of objects containing \"question\" (string) and \"type\" (string: 'Technical' or 'HR').

        {context}
        Resume Text:
        {resume_text}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            result = clean_json_response(response.choices[0].message.content.strip())
            return json.loads(result)
        except Exception as e:
            print(f"Error in generate_interview_questions: {e}")

    skills = extract_skills_from_text(resume_text)
    questions = []
    if job_description:
        questions.append({"question": "What experience do you have with the key technologies mentioned in this job description?", "type": "Technical"})
    questions.extend([
        {"question": "Tell me about a project where you solved a difficult problem.", "type": "Technical"},
        {"question": "How do you prioritize your work when deadlines are tight?", "type": "HR"},
        {"question": "Describe a time when you had to learn a new technology quickly.", "type": "HR"},
        {"question": "What tools and frameworks are you most comfortable using in your day-to-day work?", "type": "Technical"}
    ])
    return {"questions": questions[:5]}


def evaluate_interview_answer(question, answer):
    if client:
        prompt = f"""
        You are an expert interviewer. Evaluate the candidate's answer to the following question.
        Return ONLY a JSON object (no markdown formatting) with the following keys:
        - confidence_score: integer 0-100.
        - communication_score: integer 0-100.
        - technical_depth_score: integer 0-100 (if not a technical question, base this on thought process/depth).
        - suggestions: string (actionable feedback on how to improve the answer).

        Question: {question}
        Candidate Answer (transcribed from speech): {answer}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            result = clean_json_response(response.choices[0].message.content.strip())
            return json.loads(result)
        except Exception as e:
            print(f"Error in evaluate_interview_answer: {e}")

    word_count = len(answer.split())
    confidence = min(100, max(30, word_count * 5))
    communication = min(100, max(20, 100 - answer.lower().count("um") * 5))
    technical_depth = min(100, max(20, word_count * 3))
    suggestions = "Try to include concrete examples and keep your answer structured with a clear beginning, middle, and end."
    return {
        "confidence_score": confidence,
        "communication_score": communication,
        "technical_depth_score": technical_depth,
        "suggestions": suggestions
    }
