def calculated_resume_score(text, skills):
    score=0

    strengths=[]
    weaknesses=[]

    # Skills Scoring
    skill_score=min(len(skills) * 5, 30)
    score += skill_score

    if skill_score >= 20:
        strengths.append("Strong technical skills demonstrated.")
    else:
        weaknesses.append("Add more technical skills.")

    # Projects Detection
    if 'project' in text.lower():
        score += 20
        strengths.append("Project section found.")
    else:
        weaknesses.append("No project mentioned 😞.")

    # Experience Detection
    experiece_keywords=[
        'internship',
        'worked',
        'experience',
        'company'
    ]

    if any(word in text.lower() for word in experiece_keywords):
        score += 20
        strengths.append("Experience section found.")
    else:
        weaknesses.append("No 🙂‍↔️ experience mentioned 😞.")

    # Education Detection
    education_keywords=[
        'degree',
        'university',
        'college',
        'education',
        'bachelor',
        'bca'
    ]

    if any(word in text.lower() for word in education_keywords):
        score += 15
        strengths.append("Education section found 💐.")
    else:
        weaknesses.append("Education section missing.")

    # Certifications Detection
    certification_keywords=[
        'certification',
        'certified',
        'license',
        'credential',
        'certificate',
        'course'
    ]

    if any(word in text.lower() for word in certification_keywords):
        score += 15
        strengths.append("Certification found 🎓.")
    else:
        weaknesses.append("No certification added.")

    # Final Score Calculation
    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses
    }