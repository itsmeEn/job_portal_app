from django.contrib import admin
from .models import JobRecommendation, SkillsMatrix

@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'score', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'job__title')
    date_hierarchy = 'created_at'

@admin.register(SkillsMatrix)
class SkillsMatrixAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'category')
    list_filter = ('category',)
    search_fields = ('skill_name', 'category')

