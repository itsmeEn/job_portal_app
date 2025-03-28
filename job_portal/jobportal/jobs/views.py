from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.http import JsonResponse
from .models import Job, JobApplication, Company, JobCategory
from .forms import JobSearchForm, JobApplicationForm, JobPostForm
from django.db.models import Count
from django.utils import timezone
from .models import Interview
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.urls import path, include

def home(request):
    featured_jobs = Job.objects.filter(is_active=True).order_by('-posted_date')[:6]
    job_categories = JobCategory.objects.all()
    
    context = {
        'featured_jobs': featured_jobs,
        'job_categories': job_categories,
    }
    return render(request, 'jobs/home.html', context)

def job_list(request):
    form = JobSearchForm(request.GET)
    jobs = Job.objects.filter(is_active=True)
    
    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        location = form.cleaned_data.get('location')
        category = form.cleaned_data.get('category')
        job_type = form.cleaned_data.get('job_type')
        
        if keyword:
            jobs = jobs.filter(
                Q(title__icontains=keyword) | 
                Q(description__icontains=keyword) |
                Q(skills_required__icontains=keyword)
            )
        
        if location:
            jobs = jobs.filter(location__icontains=location)
        
        if category:
            jobs = jobs.filter(category=category)
        
        if job_type:
            jobs = jobs.filter(job_type=job_type)
    
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
    }
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    related_jobs = Job.objects.filter(
        category=job.category, 
        is_active=True
    ).exclude(id=job.id)[:3]
    
    # Check if user has already applied
    has_applied = False
    if request.user.is_authenticated:
        has_applied = JobApplication.objects.filter(job=job, applicant=request.user).exists()
    
    context = {
        'job': job,
        'related_jobs': related_jobs,
        'has_applied': has_applied,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('job_detail', job_id=job.id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.save()
            
            # Create notification for job poster
            from users.models import Notification
            Notification.objects.create(
                user=job.posted_by,
                notification_type='NEW_APPLICATION',
                title='New Job Application',
                message=f'{request.user.username} has applied for {job.title}',
                link=f'/jobs/{job.id}/'
            )
            
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobApplicationForm()
    
    context = {
        'form': form,
        'job': job,
    }
    return render(request, 'jobs/apply_job.html', context)

@login_required
def post_job(request):
    # Check if user is a recruiter
    if request.user.profile.role != 'RECRUITER':
        messages.warning(request, 'You need to be a recruiter to post jobs.')
        return redirect('role_selection')
    
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            
            # If AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'job': {
                        'id': job.id,
                        'title': job.title,
                        'company_name': job.company.name,
                        'job_type_display': job.get_job_type_display(),
                        'location': job.location,
                        'url': reverse('job_detail', args=[job.id])
                    }
                })
            
            messages.success(request, 'Job posted successfully!')
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobPostForm()
    
    context = {
        'form': form,
    }
    return render(request, 'jobs/post_job.html', context)

@login_required
def my_jobs(request):
    # Check if user is a recruiter
    if request.user.profile.role != 'RECRUITER' and not request.user.is_staff:
        messages.warning(request, 'You need to be a recruiter to access this page.')
        return redirect('role_selection')
    
    posted_jobs = Job.objects.filter(posted_by=request.user)
    applications = JobApplication.objects.filter(applicant=request.user)
    
    context = {
        'posted_jobs': posted_jobs,
        'applications': applications,
    }
    return render(request, 'jobs/my_jobs.html', context)

@login_required
def application_dashboard(request):
    # Check if user is an applicant
    if request.user.profile.role != 'APPLICANT' and not request.user.is_staff:
        messages.warning(request, 'You need to be a job seeker to access this page.')
        return redirect('role_selection')
    
    # For job seekers
    applications = JobApplication.objects.filter(applicant=request.user)
    
    # Group by status
    pending = applications.filter(status='PENDING')
    reviewing = applications.filter(status='REVIEWING')
    shortlisted = applications.filter(status='SHORTLISTED')
    rejected = applications.filter(status='REJECTED')
    accepted = applications.filter(status='ACCEPTED')
    
    # Get upcoming interviews
    interviews = Interview.objects.filter(
        application__applicant=request.user,
        scheduled_date__gte=timezone.now(),
        status='SCHEDULED'
    ).order_by('scheduled_date')
    
    context = {
        'applications': applications,
        'pending': pending,
        'reviewing': reviewing,
        'shortlisted': shortlisted,
        'rejected': rejected,
        'accepted': accepted,
        'interviews': interviews,
    }
    return render(request, 'jobs/application_dashboard.html', context)

@login_required
def employer_dashboard(request):
    # Check if user is a recruiter
    if request.user.profile.role != 'RECRUITER' and not request.user.is_staff:
        messages.warning(request, 'You need to be a recruiter to access this page.')
        return redirect('role_selection')
    
    # Get jobs posted by the user
    jobs = Job.objects.filter(posted_by=request.user)
    
    # Get applications for those jobs
    applications = JobApplication.objects.filter(job__in=jobs)
    
    # Count applications by status
    status_counts = applications.values('status').annotate(count=Count('status'))
    
    # Get recent applications
    recent_applications = applications.order_by('-applied_date')[:10]
    
    # Get upcoming interviews
    interviews = Interview.objects.filter(
        application__job__posted_by=request.user,
        scheduled_date__gte=timezone.now(),
        status='SCHEDULED'
    ).order_by('scheduled_date')
    
    context = {
        'jobs': jobs,
        'applications': applications,
        'status_counts': status_counts,
        'recent_applications': recent_applications,
        'interviews': interviews,
    }
    return render(request, 'jobs/employer_dashboard.html', context)


#added this to show the success page after posting a job
def job_post_success(request):
    # This view can be used to show a success message after posting a job
    if request.method == 'POST':
        messages.success(request, 'Job posted successfully!')
        return redirect('home')
    else:
        messages.error(request, 'Invalid request method.')
    
    return render(request, 'jobs/job_post_success.html')