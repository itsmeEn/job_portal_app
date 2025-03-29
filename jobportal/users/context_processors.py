from django.db.models import Q

def conversation_processor(request):
    if request.user.is_authenticated:
        recent_conversations = request.user.conversations.all().order_by('-updated_at')[:5]
    else:
        recent_conversations = []
    
    return {
        'recent_conversations': recent_conversations,
    } 