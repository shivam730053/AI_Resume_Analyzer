from .skill_extractor import extract_skills

def match_resume_with_job_description(resume_text, job_description):
    resume_skills = extract_skills(resume_text)
    job_skills = extract_skills(job_description)

    matched_skills = []
    missing_skills = []
    for skill in job_skills:
        if skill in resume_skills:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    if len(job_skills) == 0:
        match_percentage = 0
    else:
        match_percentage = int(len(matched_skills) / len(job_skills)) * 100

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage
    }