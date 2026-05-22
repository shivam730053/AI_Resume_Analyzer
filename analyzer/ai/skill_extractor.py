import spacy

nlp = spacy.load("en_core_web_sm")

SKILLS = ["python","java","c","c++","django","flask","sql","mysql","mongodb","html",
    "css","javascript","react","nodejs","machine learning","data science","git","github","linux","docker"]

def extract_skills(text):
    doc = nlp(text.lower())
    found_skills = set()
    for token in doc:
        if token.lemma_ in SKILLS:
            found_skills.add(token.lemma_)
        for skills in SKILLS:
            if skills in text.lower():
                found_skills.add(skills)

    return found_skills
