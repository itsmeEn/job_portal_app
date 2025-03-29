from django import template

register = template.Library()

@register.filter
def other_participant(conversation, user):
    """Get the other participant in a conversation."""
    return conversation.participants.exclude(id=user.id).first() 