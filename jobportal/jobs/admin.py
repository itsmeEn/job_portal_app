from django.contrib import admin
from .models import Company, JobCategory, Job, JobApplication, Interview

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'website', 'created_at')
    search_fields = ('name', 'location')

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'job_type', 'experience_level', 'is_active', 'posted_date')
    list_filter = ('is_active', 'job_type', 'experience_level', 'category')
    search_fields = ('title', 'company__name', 'location', 'description')
    date_hierarchy = 'posted_date'

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'applied_date', 'updated_date')
    list_filter = ('status', 'applied_date')
    search_fields = ('job__title', 'applicant__username', 'applicant__email')
    date_hierarchy = 'applied_date'

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_date', 'status', 'is_virtual', 'created_at')
    list_filter = ('status', 'is_virtual', 'scheduled_date')
    search_fields = ('application__job__title', 'application__applicant__username')
    date_hierarchy = 'scheduled_date'

