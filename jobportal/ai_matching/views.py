from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .services import JobMatchingService
from .models import JobRecommendation

@login_required
def job_recommendations(request):
    # Get existing recommendations or generate new ones
    recommendations = JobRecommendation.objects.filter(user=request.user)
    
    if not recommendations.exists():
        # Generate new recommendations
        matching_service = JobMatchingService()
        matching_service.generate_recommendations(request.user)
        recommendations = JobRecommendation.objects.filter(user=request.user)
    
    context = {
        'recommendations': recommendations,
    }
    return render(request, 'ai_matching/recommendations.html', context)

@login_required
def refresh_recommendations(request):
    # Force regenerate recommendations
    matching_service = JobMatchingService()
    matching_service.generate_recommendations(request.user)
    
    return redirect('job_recommendations')

@login_required
def skill_analysis(request):
    # Analyze user's skills and suggest improvements
    user_profile = request.user.profile
    skills = user_profile.skills.split(',') if user_profile.skills else []
    
    # Get top skills in demand from jobs
    from django.db.models import Count
    from jobs.models import Job
    
    all_job_skills = []
    for job in Job.objects.filter(is_active=True):
        if job.skills_required:
            all_job_skills.extend([s.strip() for s in job.skills_required.split(',')])
    
    from collections import Counter
    skill_counts = Counter(all_job_skills)
    top_skills = skill_counts.most_common(10)
    
    # Find skills gap
    user_skills_set = {s.strip().lower() for s in skills}
    top_skills_set = {s[0].lower() for s in top_skills}
    missing_skills = top_skills_set - user_skills_set
    
    context = {
        'user_skills': skills,
        'top_skills': top_skills,
        'missing_skills': missing_skills,
    }
    return render(request, 'ai_matching/skill_analysis.html', context)

