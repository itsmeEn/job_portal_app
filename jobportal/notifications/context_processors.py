from .models import Notification

def notification_processor(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    else:
        unread_count = 0
        recent_notifications = []
    
    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
    } 