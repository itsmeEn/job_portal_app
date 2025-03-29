from django.db import models
from django.contrib.auth.models import User
from jobs.models import Job

class JobRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_recommendations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.job.title} ({self.score})"
    
    class Meta:
        ordering = ['-score']
        unique_together = ('user', 'job')

class SkillsMatrix(models.Model):
    skill_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.skill_name

