from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('APPLICATION_STATUS', 'Application Status Change'),
        ('NEW_APPLICATION', 'New Application'),
        ('INTERVIEW_SCHEDULED', 'Interview Scheduled'),
        ('JOB_RECOMMENDATION', 'Job Recommendation'),
        ('MESSAGE', 'New Message'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

