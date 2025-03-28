from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import UserProfile, Notification, Conversation, Message, ChatbotConversation, ChatbotMessage
from .forms import UserProfileForm, MessageForm, ChatbotMessageForm, RecruiterSignupForm
from jobs.models import JobApplication, Job, Interview, Company
from ai_matching.models import JobRecommendation
import json
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

def home(request):
    # If user is logged in and has a role, redirect to appropriate dashboard
    if request.user.is_authenticated and request.user.profile.role:
        if request.user.profile.role == 'APPLICANT':
            return redirect('applicant_dashboard')
        else:
            return redirect('recruiter_dashboard')
    
    # Otherwise show the home page
    from jobs.views import home as jobs_home
    return jobs_home(request)

def applicant_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Set user role to applicant
                profile = user.profile
                profile.role = 'APPLICANT'
                profile.save()
                
                messages.success(request, f"Welcome back, {username}!")
                return redirect('applicant_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/applicant_login.html', {'form': form})

def recruiter_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Set user role to recruiter
                profile = user.profile
                profile.role = 'RECRUITER'
                profile.save()
                
                messages.success(request, f"Welcome back, {username}!")
                return redirect('recruiter_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/recruiter_login.html', {'form': form})

def applicant_signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Set user role to applicant
            profile = user.profile
            profile.role = 'APPLICANT'
            profile.save()
            
            # Log the user in
            login(request, user)
            messages.success(request, f"Account created for {username}. Welcome to AI Job Portal!")
            return redirect('applicant_dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'users/applicant_signup.html', {'form': form})

def recruiter_signup(request):
    if request.method == 'POST':
        form = RecruiterSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            company_name = form.cleaned_data.get('company_name')
            
            # Set user role to recruiter
            profile = user.profile
            profile.role = 'RECRUITER'
            profile.save()
            
            # Create company for the recruiter
            company = Company.objects.create(
                name=company_name,
                description=f"{company_name} description",
                location="Location not specified"
            )
            
            # Log the user in
            login(request, user)
            messages.success(request, f"Account created for {username}. Welcome to AI Job Portal!")
            return redirect('recruiter_dashboard')
    else:
        form = RecruiterSignupForm()
    
    return render(request, 'users/recruiter_signup.html', {'form': form})

@login_required
def set_applicant_role(request):
    profile = request.user.profile
    profile.role = 'APPLICANT'
    profile.save()
    
    messages.success(request, "You are now using the platform as a Job Seeker")
    return redirect('applicant_dashboard')

@login_required
def set_recruiter_role(request):
    profile = request.user.profile
    profile.role = 'RECRUITER'
    profile.save()
    
    messages.success(request, "You are now using the platform as a Recruiter")
    return redirect('recruiter_dashboard')

@login_required
def role_selection(request):
    # If user already has a role, redirect to appropriate dashboard
    if request.user.profile.role:
        if request.user.profile.role == 'APPLICANT':
            return redirect('applicant_dashboard')
        else:
            return redirect('recruiter_dashboard')
    
    return render(request, 'users/role_selection.html')

@login_required
def set_role(request):
    role = request.GET.get('role')
    
    if role in ['applicant', 'recruiter']:
        profile = request.user.profile
        profile.role = 'APPLICANT' if role == 'applicant' else 'RECRUITER'
        profile.save()
        
        messages.success(request, f'You are now using the platform as a {role.capitalize()}')
        
        if role == 'applicant':
            return redirect('applicant_dashboard')
        else:
            return redirect('recruiter_dashboard')
    
    return redirect('role_selection')

@login_required
def applicant_dashboard(request):
    # Check if user is an applicant
    if request.user.profile.role != 'APPLICANT' and not request.user.is_staff:
        messages.warning(request, 'You need to be a job seeker to access this page.')
        return redirect('set_applicant_role')
    
    # Get applications
    applications = JobApplication.objects.filter(applicant=request.user)
    
    # Get recommendations
    recommendations = JobRecommendation.objects.filter(user=request.user).order_by('-score')
    
    # Get upcoming interviews
    interviews = Interview.objects.filter(
        application__applicant=request.user,
        scheduled_date__gte=timezone.now(),
        status='SCHEDULED'
    ).order_by('scheduled_date')
    
    # Calculate profile strength
    profile = request.user.profile
    profile_strength = 0
    
    if profile.bio:
        profile_strength += 10
    if profile.profile_picture:
        profile_strength += 10
    if profile.resume:
        profile_strength += 20
    if profile.skills:
        profile_strength += 15
    if profile.experience:
        profile_strength += 15
    if profile.education:
        profile_strength += 15
    if profile.location:
        profile_strength += 5
    if profile.phone_number:
        profile_strength += 5
    if profile.linkedin_profile or profile.github_profile or profile.website:
        profile_strength += 5
    
    context = {
        'applications': applications,
        'recommendations': recommendations,
        'interviews': interviews,
        'profile_strength': profile_strength
    }
    
    return render(request, 'users/applicant_dashboard.html', context)

@login_required
def recruiter_dashboard(request):
    # Check if user is a recruiter
    if request.user.profile.role != 'RECRUITER' and not request.user.is_staff:
        messages.warning(request, 'You need to be a recruiter to access this page.')
        return redirect('set_recruiter_role')
    
    # Get jobs posted by the user
    jobs = Job.objects.filter(posted_by=request.user)
    
    # Get applications for those jobs
    applications = JobApplication.objects.filter(job__in=jobs)
    
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
        'recent_applications': recent_applications,
        'interviews': interviews,
    }
    
    return render(request, 'users/recruiter_dashboard.html', context)

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

# Chatbot views
@login_required
def chatbot(request):
    # Get all chatbot conversations for the user
    conversations = ChatbotConversation.objects.filter(user=request.user)
    
    # Get or create active conversation
    active_conversation_id = request.session.get('active_chatbot_conversation')
    active_conversation = None
    
    if active_conversation_id:
        try:
            active_conversation = ChatbotConversation.objects.get(id=active_conversation_id, user=request.user)
        except ChatbotConversation.DoesNotExist:
            active_conversation = None
    
    if not active_conversation and conversations.exists():
        active_conversation = conversations.first()
    elif not active_conversation:
        # Create a new conversation
        active_conversation = ChatbotConversation.objects.create(
            user=request.user,
            title="Resume Help"
        )
        
        # Add welcome message
        ChatbotMessage.objects.create(
            conversation=active_conversation,
            message_type='BOT',
            content="Hello! I'm your AI resume assistant. I can help you improve your resume, prepare for interviews, or answer questions about job applications. How can I help you today?"
        )
    
    # Set active conversation in session
    request.session['active_chatbot_conversation'] = active_conversation.id
    
    # Get messages for active conversation
    messages = ChatbotMessage.objects.filter(conversation=active_conversation)
    
    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages,
        'form': ChatbotMessageForm(),
    }
    return render(request, 'users/chatbot.html', context)

@login_required
def new_chatbot_conversation(request):
    # Create a new conversation
    conversation = ChatbotConversation.objects.create(
        user=request.user,
        title="New Conversation"
    )
    
    # Add welcome message
    ChatbotMessage.objects.create(
        conversation=conversation,
        message_type='BOT',
        content="Hello! I'm your AI resume assistant. I can help you improve your resume, prepare for interviews, or answer questions about job applications. How can I help you today?"
    )
    
    # Set as active conversation
    request.session['active_chatbot_conversation'] = conversation.id
    
    return redirect('chatbot')

@login_required
def select_chatbot_conversation(request, conversation_id):
    conversation = get_object_or_404(ChatbotConversation, id=conversation_id, user=request.user)
    request.session['active_chatbot_conversation'] = conversation.id
    return redirect('chatbot')

@login_required
@require_POST
def send_chatbot_message(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        conversation_id = request.session.get('active_chatbot_conversation')
        if not conversation_id:
            return JsonResponse({'error': 'No active conversation'}, status=400)
        
        try:
            conversation = ChatbotConversation.objects.get(id=conversation_id, user=request.user)
        except ChatbotConversation.DoesNotExist:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
        
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Save user message
        ChatbotMessage.objects.create(
            conversation=conversation,
            message_type='USER',
            content=user_message
        )
        
        # Generate bot response based on user message
        bot_response = generate_chatbot_response(user_message, request.user)
        
        # Save bot response
        bot_message = ChatbotMessage.objects.create(
            conversation=conversation,
            message_type='BOT',
            content=bot_response
        )
        
        # Update conversation
        conversation.updated_at = bot_message.created_at
        if conversation.title == "New Conversation":
            # Update title based on first user message
            conversation.title = user_message[:30] + "..." if len(user_message) > 30 else user_message
        conversation.save()
        
        return JsonResponse({
            'user_message': {
                'content': user_message,
                'created_at': ChatbotMessage.objects.filter(conversation=conversation, message_type='USER').last().created_at.strftime('%b %d, %Y, %I:%M %p')
            },
            'bot_message': {
                'content': bot_response,
                'created_at': bot_message.created_at.strftime('%b %d, %Y, %I:%M %p')
            }
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def generate_chatbot_response(user_message, user):
    """Generate a response from the chatbot based on the user's message"""
    user_message_lower = user_message.lower()
    
    # Resume improvement
    if any(keyword in user_message_lower for keyword in ['resume', 'cv', 'improve', 'help with resume']):
        return """I'd be happy to help with your resume! Here are some tips to make it stand out:

1. **Tailor your resume** to each job application by matching keywords from the job description
2. **Quantify your achievements** with numbers and metrics when possible
3. **Use action verbs** at the beginning of bullet points (e.g., "Implemented," "Developed," "Managed")
4. **Keep it concise** - aim for 1 page for early career, 2 pages maximum for experienced professionals
5. **Include a skills section** highlighting technical and soft skills relevant to the position

Would you like more specific advice on a particular section of your resume?"""
    
    # Interview preparation
    elif any(keyword in user_message_lower for keyword in ['interview', 'prepare', 'questions']):
        return """Preparing for interviews is crucial! Here are some tips:

1. **Research the company** thoroughly - understand their products, culture, and recent news
2. **Practice common questions** like "Tell me about yourself" and "Why do you want to work here?"
3. **Use the STAR method** for behavioral questions (Situation, Task, Action, Result)
4. **Prepare thoughtful questions** to ask the interviewer
5. **Do mock interviews** with friends or record yourself to improve your delivery

Would you like some sample questions for a specific role or industry?"""
    
    # Job search advice
    elif any(keyword in user_message_lower for keyword in ['job search', 'find job', 'application']):
        return """Here are some effective job search strategies:

1. **Optimize your online profiles** - especially LinkedIn
2. **Network actively** - reach out to connections and attend industry events
3. **Set up job alerts** on multiple platforms to stay informed of new opportunities
4. **Follow up** after submitting applications (typically 1-2 weeks later)
5. **Track your applications** to stay organized
6. **Consider working with recruiters** in your industry

Is there a specific aspect of your job search you'd like more advice on?"""
    
    # Skills assessment
    elif any(keyword in user_message_lower for keyword in ['skills', 'improve skills', 'learn']):
        return """Developing your skills is a great investment! Here's how to approach it:

1. **Identify skill gaps** by comparing your current skills with job descriptions
2. **Prioritize learning** based on industry demand and your interests
3. **Take online courses** through platforms like Coursera, Udemy, or LinkedIn Learning
4. **Work on projects** to apply what you've learned
5. **Get certifications** that are recognized in your industry
6. **Join communities** where you can learn from others

What specific skills are you looking to develop?"""
    
    # Cover letter help
    elif any(keyword in user_message_lower for keyword in ['cover letter', 'letter']):
        return """A strong cover letter can set you apart! Here are my tips:

1. **Address it to a specific person** whenever possible
2. **Open with an attention-grabbing introduction** that shows your enthusiasm
3. **Highlight 2-3 key achievements** relevant to the position
4. **Explain why you're interested** in both the role and the company
5. **Keep it to one page** and use a professional tone
6. **End with a clear call to action** expressing interest in an interview

Would you like a template or help with a specific section of your cover letter?"""
    
    # Salary negotiation
    elif any(keyword in user_message_lower for keyword in ['salary', 'negotiate', 'offer']):
        return """Salary negotiation is an important skill! Here's how to approach it:

1. **Research salary ranges** for your role, experience level, and location
2. **Wait for the employer to mention salary** first if possible
3. **Consider the entire compensation package** including benefits, not just base salary
4. **Practice your negotiation** with specific numbers and justification
5. **Be professional and collaborative** in your approach
6. **Get the final offer in writing** before accepting

Would you like specific phrases to use during your negotiation?"""
    
    # Default response
    else:
        return """I'm here to help with your job search and career development! I can assist with:

- Resume and cover letter improvement
- Interview preparation
- Job search strategies
- Skills development
- Salary negotiation
- Career transitions

What specific aspect would you like help with today?"""

