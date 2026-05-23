from django.shortcuts import render, redirect
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
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test


def is_staff(user):
    return user.is_authenticated and user.is_staff

def home(request):
    """
    Landing page.
    Passes live stats so the KPI row shows real numbers.
    Falls back gracefully when the Resume table is empty.
    """
    total_resumes = Resume.objects.count()
 
    avg_score = Resume.objects.aggregate(avg=Avg('score'))['avg']
    avg_match = Resume.objects.aggregate(avg=Avg('match_percentage'))['avg']
    average_score = round(avg_score, 1) if avg_score else 0
    average_match = round(avg_match, 1) if avg_match else 0
 
    # Top 6 skills for the "Most in-demand skills" badge row
    all_skills = (
        Resume.objects
        .values_list('extracted_skills', flat=True)
        .exclude(extracted_skills__isnull=True)
        .exclude(extracted_skills='')
    )
    skill_counts = {}
    for skill_str in all_skills:
        for skill in skill_str.split(','):
            s = skill.strip()
            if s:
                skill_counts[s] = skill_counts.get(s, 0) + 1
 
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:6]
 
    return render(request, 'analyzer/home.html', {
        'total_resumes': total_resumes,
        'average_score': average_score,
        'average_match': average_match,
        'top_skills':    top_skills,
    })


def logout_view(request):
    """
    Logs the user out and redirects to the logout confirmation page.
    Accepts GET and POST (POST preferred for CSRF safety).
    """
    logout(request)
    return redirect('logout_confirm')


def login_view(request):
    """
    GET  → show login form.
    POST → authenticate; on success redirect to ?next or resume_upload.
    """
    if request.user.is_authenticated:
        return redirect('resume_upload')
 
    form = AuthenticationForm(request, data=request.POST or None)
 
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or 'resume_upload'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
 
    return render(request, 'analyzer/login.html', {'form': form})


def logout_confirm(request):
    features = [
        "Resume scoring out of 100",
        "Job match percentage",
        "Skill gap detection",
        "Strengths and weaknesses",
        "PDF report download",
        "Results in under 10 seconds"
    ]
    return render(request, 'analyzer/logout.html', {'features': features})


def register_view(request):
    """
    User registration with Django's built-in UserCreationForm.
    On success logs the user in and redirects to resume_upload.
    """
    if request.user.is_authenticated:
        return redirect('resume_upload')
 
    form = UserCreationForm(request.POST or None)
 
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('resume_upload')
        else:
            messages.error(request, 'Please fix the errors below.')
 
    return render(request, 'analyzer/register.html', {'form': form})
 

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


# @user_passes_test(is_staff, login_url='login')
def dashboard(request):
    """
    Admin-only analytics dashboard.
    Non-staff users are redirected to the login page.
    """
    total_resumes = Resume.objects.count()
 
    avg_score = Resume.objects.aggregate(avg=Avg('score'))['avg']
    avg_match = Resume.objects.aggregate(avg=Avg('match_percentage'))['avg']
    average_score = round(avg_score, 1) if avg_score else 0
    average_match = round(avg_match, 1) if avg_match else 0
 
    # ── Top skills ────────────────────────────────────────────────────────
    all_skills = (
        Resume.objects
        .values_list('extracted_skills', flat=True)
        .exclude(extracted_skills__isnull=True)
        .exclude(extracted_skills='')
    )
    skill_counts = {}
    for skill_str in all_skills:
        for skill in skill_str.split(','):
            s = skill.strip()
            if s:
                skill_counts[s] = skill_counts.get(s, 0) + 1
 
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
 
    # ── Recent uploads ────────────────────────────────────────────────────
    recent_resumes = Resume.objects.order_by('-uploaded_at')[:8]
 
    # ── Score distribution buckets ────────────────────────────────────────
    buckets     = {'0–20': 0, '20–40': 0, '40–60': 0, '60–80': 0, '80–100': 0}
    bucket_keys = list(buckets.keys())
    for score_val in Resume.objects.values_list('score', flat=True):
        if score_val is not None:
            idx = min(int(score_val) // 20, 4)
            buckets[bucket_keys[idx]] += 1
 
    # ── Upload trend — last 7 days ────────────────────────────────────────
    today = timezone.now().date()
    trend = {}
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        trend[day.strftime('%a')] = 0
 
    recent = Resume.objects.filter(uploaded_at__date__gte=today - timedelta(days=6))
    for resume in recent:
        label = resume.uploaded_at.strftime('%a')
        if label in trend:
            trend[label] += 1
 
    return render(request, 'analyzer/dashboard.html', {
        'total_resumes':             total_resumes,
        'average_score':             average_score,
        'average_match':             average_match,
        'top_skills':                top_skills,
        'recent_resumes':            recent_resumes,
        'score_distribution_labels': json.dumps(list(buckets.keys())),
        'score_distribution_counts': json.dumps(list(buckets.values())),
        'trend_labels':              json.dumps(list(trend.keys())),
        'trend_counts':              json.dumps(list(trend.values())),
    })
 
