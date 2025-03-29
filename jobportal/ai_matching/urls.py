from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.job_recommendations, name='job_recommendations'),
    path('recommendations/refresh/', views.refresh_recommendations, name='refresh_recommendations'),
    path('skill-analysis/', views.skill_analysis, name='skill_analysis'),
]

