from django.shortcuts import render
from django.http import HttpResponse
from .models import Resume
from .utils import extract_text_from_pdf
from .ai.skill_extractor import extract_skills
from .ai.scorer import calculated_resume_score
from .ai.matcher import match_resume_with_job_description
from .ai.pdf_generator import generate_pdf_report
 
 
def resume_upload(request):
    if request.method == "POST":
        file = request.FILES.get('resume')
        job_description = request.POST.get('job_description')
 
        if file and job_description:
            obj = Resume.objects.create(file=file)
            text = extract_text_from_pdf(obj.file.path)
 
            skills  = extract_skills(text)
            result  = calculated_resume_score(text, skills)
            match   = match_resume_with_job_description(text, job_description)
 
            return render(request, 'analyzer/success.html', {
                'text':             text,
                'skills':           skills,
                'score':            result['score'],
                'strengths':        result['strengths'],
                'weaknesses':       result['weaknesses'],
                'match_percentage': match['match_percentage'],
                'match_skills':     match['matched_skills'],
                'missing_skills':   match['missing_skills'],
            })
 
    return render(request, 'analyzer/upload.html')
 
 
def download_pdf(request):
    # ── Pull all list params correctly with getlist() ──────────────────────
    score            = request.GET.get('score', '0')
    match_percentage = request.GET.get('match_percentage', '0')   # was 'match_request' — typo fixed
    skills           = request.GET.getlist('skills')               # was .get() — returned a string
    match_skills     = request.GET.getlist('match_skills')
    missing_skills   = request.GET.getlist('missing_skills')
    strengths        = request.GET.getlist('strengths')            # was .get() — returned a string
    weaknesses       = request.GET.getlist('weaknesses')           # was .get() — returned a string
 
    # ── Generate PDF into an in-memory buffer (no temp file needed) ────────
    pdf_buffer = generate_pdf_report(
        score=score,
        match_percentage=match_percentage,
        skills=skills,
        match_skills=match_skills,
        missing_skills=missing_skills,
        strengths=strengths,
        weaknesses=weaknesses,
    )
 
    # ── Stream directly to the browser ────────────────────────────────────
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="resume_analysis_report.pdf"'
    return response
 
