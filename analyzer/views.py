from django.shortcuts import render
from django.http import HttpResponse
from .models import Resume
from .utils import extract_text
from .ai.skill_extractor import extract_skills
from .ai.scorer import calculated_resume_score
from .ai.matcher import match_resume_with_job_description
from .ai.pdf_generator import generate_pdf_report
import os
from django.db.models import Avg
from collections import Counter
import json
from datetime import timedelta
from django.utils import timezone

def resume_upload(request):
    if request.method == "POST":
        file = request.FILES.get('resume')
        allowed_extensions=[
            '.pdf',
            '.docx',
            '.txt'
        ]

        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return render(request, 'analyzer/upload.html', {
                'error': 'Unsupported file format. Please upload a PDF, DOCX, or TXT file.'
            })

        job_description = request.POST.get('job_description')
 
        if file and job_description:
            obj = Resume.objects.create(file=file)
            text = extract_text(obj.file.path)
            skills = extract_skills(text)
            result = calculated_resume_score(text, skills)
            match = match_resume_with_job_description(text, job_description)

            # Save calculated fields to the Resume object
            obj.score = result['score']
            obj.match_percentage = match['match_percentage']
            obj.extracted_skills = ", ".join(skills)
            obj.save()

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
 
def dashboard(request):
    resumes=Resume.objects.all()
    total_resumes=resumes.count()
    average_score=resumes.aggregate(
        Avg('score'),
    )['score__avg']

    average_match_percentage=resumes.aggregate(
        Avg('match_percentage'),
    )['match_percentage__avg']

    all_skills=[]

    for resume in resumes:
        all_skills.extend(resume.extracted_skills.split(','))

    skill_counter = Counter(all_skills)
    top_skills = skill_counter.most_common(5)

    recent_resumes = resumes.order_by('-uploaded_at')[:5]

    buckets = {'0–20': 0, '20–40': 0, '40–60': 0, '60–80': 0, '80–100': 0}
    for r in Resume.objects.values_list('score', flat=True):
        if r is not None:
            key = ['0–20','20–40','40–60','60–80','80–100'][min(int(r) // 20, 4)]
            buckets[key] += 1

    # Upload trend (last 7 days)
    today = timezone.now().date()
    trend = {(today - timedelta(days=i)).strftime('%a'): 0 for i in range(6, -1, -1)}
    for r in Resume.objects.filter(uploaded_at__date__gte=today - timedelta(days=6)):
        trend[r.uploaded_at.strftime('%a')] += 1

    return render(request, 'analyzer/dashboard.html', {
        'total_resumes': total_resumes,
        'average_score': round(average_score or 0, 2),
        'average_match_percentage': round(average_match_percentage or 0, 2),
        'top_skills': top_skills,
        'recent_resumes': recent_resumes,
        'score_distribution_labels': json.dumps(list(buckets.keys())),
        'score_distribution_counts': json.dumps(list(buckets.values())),
        'trend_labels': json.dumps(list(trend.keys())),
        'trend_counts': json.dumps(list(trend.values())),
    })