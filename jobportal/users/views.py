from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from .models import UserProfile, Notification, Conversation, Message
from .forms import UserProfileForm, MessageForm
from jobs.models import JobApplication

@login_required
def profile(request):
    user_profile = request.user.profile
    applications = JobApplication.objects.filter(applicant=request.user)
    
    # Get unread notifications
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    context = {
        'profile': user_profile,
        'applications': applications,
        'notifications': notifications,
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            
            # Update user model fields if provided
            user = request.user
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                user.email = email
            
            user.save()
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'users/edit_profile.html', context)

@login_required
def notifications(request):
    # Get all notifications for the user
    user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read
    unread_notifications = user_notifications.filter(is_read=False)
    for notification in unread_notifications:
        notification.is_read = True
        notification.save()
    
    context = {
        'notifications': user_notifications,
    }
    return render(request, 'users/notifications.html', context)

@login_required
def message_list(request):
    # Get all conversations for the user
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'users/message_list.html', context)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    messages_list = conversation.messages.all().order_by('created_at')
    
    # Get the other participant
    other_participant = conversation.participants.exclude(id=request.user.id).first()
    
    # Mark messages as read
    unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
    for message in unread_messages:
        message.is_read = True
        message.save()
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            
            # Create new message
            new_message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # Update conversation timestamp
            conversation.save()  # This will update the updated_at field
            
            # Create notification for the other participant
            if other_participant:
                Notification.objects.create(
                    user=other_participant,
                    notification_type='MESSAGE',
                    title='New Message',
                    message=f'You have a new message from {request.user.username}',
                    link=f'/users/messages/{conversation.id}/'
                )
            
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_participant': other_participant,
        'form': form,
    }
    return render(request, 'users/conversation_detail.html', context)

@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
    
    if existing_conversation.exists():
        # Use existing conversation
        conversation = existing_conversation.first()
    else:
        # Create new conversation
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def public_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    
    context = {
        'profile_user': user,
        'profile': profile,
    }
    return render(request, 'users/public_profile.html', context)

@login_required
def some_view(request):
    unread_notifications = request.user.notifications.filter(is_read=False)  # Filtering in Python
    return render(request, "navbar.html", {"unread_notifications": unread_notifications})
