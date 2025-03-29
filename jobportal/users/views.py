from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.backends import ModelBackend
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.middleware.csrf import get_token
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token
from .models import UserProfile, Conversation, Message, ChatbotConversation, ChatbotMessage
from notifications.models import Notification
from .forms import UserProfileForm, MessageForm, ChatbotMessageForm, RecruiterSignupForm
from jobs.models import JobApplication, Job, Interview, Company
from ai_matching.models import JobRecommendation
from django.utils import timezone
import json

def home(request):
    # If user is logged in, redirect to appropriate dashboard based on role
    if request.user.is_authenticated:
        if request.user.profile.role == 'APPLICANT':
            return redirect('users:applicant_dashboard')
        elif request.user.profile.role == 'RECRUITER':
            return redirect('users:recruiter_dashboard')
    
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
                # Get or create profile if it doesn't exist
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Check if user is active
                if not user.is_active:
                    messages.error(request, "Your account is not activated. Please check your email for the activation link.")
                    return redirect('users:applicant_login')
                
                # Check if user is an applicant or if role is not set
                if profile.role == 'APPLICANT' or not profile.role:
                    # Set role to APPLICANT if not set
                    if not profile.role:
                        profile.role = 'APPLICANT'
                        profile.save()
                    
                    login(request, user)
                    messages.success(request, f"Welcome back, {username}!")
                    return redirect('users:applicant_dashboard')
                else:
                    messages.error(request, "This account is not registered as a job seeker.")
                    return redirect('users:applicant_login')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        # Add Bootstrap classes to form fields
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget.attrs.update({'class': 'form-control'})
    
    return render(request, 'users/applicant_login.html', {'form': form})

@ensure_csrf_cookie
@csrf_protect
def recruiter_login(request):
    """
    Handle recruiter login with proper CSRF protection
    """
    # Set CSRF cookie
    get_token(request)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if user is a recruiter
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Check if user is active
                if not user.is_active:
                    messages.error(request, "Your account is not activated. Please check your email for the activation link.")
                    return redirect('users:recruiter_login')
                
                if profile.role != 'RECRUITER':
                    messages.error(request, "This account is not registered as a recruiter.")
                    return redirect('users:recruiter_login')
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f"Welcome back, {username}!")
                
                next_url = request.GET.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('users:recruiter_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        # Add Bootstrap classes to form fields
        form.fields['username'].widget.attrs.update({'class': 'form-control'})
        form.fields['password'].widget.attrs.update({'class': 'form-control'})
    
    response = render(request, 'users/recruiter_login.html', {'form': form})
    response.set_cookie('csrftoken', get_token(request))
    return response

def send_verification_email(request, user, to_email):
    current_site = get_current_site(request)
    mail_subject = 'Activate your Worksy account'
    message = render_to_string('users/account_activation_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html'
    email.send()

def applicant_signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account till it is verified
            user.save()
            
            # Set user role to applicant
            profile = UserProfile.objects.get(user=user)
            profile.role = 'APPLICANT'
            profile.save()
            
            # Send verification email
            send_verification_email(request, user, form.cleaned_data.get('email'))
            
            messages.success(request, 'Please confirm your email address to complete the registration.')
            return redirect('users:applicant_login')
    else:
        form = UserCreationForm()
    
    return render(request, 'users/applicant_signup.html', {'form': form})

@ensure_csrf_cookie
@csrf_protect
def recruiter_signup(request):
    if request.method == 'POST':
        form = RecruiterSignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                user.is_active = False  # Deactivate account till it is verified
                user.save()
                
                username = form.cleaned_data.get('username')
                company_name = form.cleaned_data.get('company_name')
                email = form.cleaned_data.get('email')
                
                # Set user role to recruiter
                profile = user.profile
                profile.role = 'RECRUITER'
                
                # Create company for the recruiter
                company = Company.objects.create(
                    name=company_name,
                    description=f"{company_name} description",
                    location="Location not specified"
                )
                
                # Associate company with user profile
                profile.company = company
                profile.save()
                
                # Send verification email
                send_verification_email(request, user, email)
                
                messages.success(request, 'Please confirm your email address to complete the registration.')
                return redirect('users:recruiter_login')
            except Exception as e:
                messages.error(request, f"Error creating account: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RecruiterSignupForm()
    
    return render(request, 'users/recruiter_signup.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        # Ensure user has a profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Activate the user
        user.is_active = True
        user.save()
        
        # Log the user in with the specific backend
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Thank you for confirming your email. Your account is now active!')
        
        # Redirect based on user role
        if profile.role == 'RECRUITER':
            return redirect('users:recruiter_dashboard')
        elif profile.role == 'APPLICANT':
            return redirect('users:applicant_dashboard')
        else:
            # If no role is set, set it to APPLICANT by default
            profile.role = 'APPLICANT'
            profile.save()
            return redirect('users:applicant_dashboard')
    else:
        messages.error(request, 'Activation link is invalid or has expired!')
        return redirect('users:home')

@login_required
def applicant_dashboard(request):
    # Check if user is an applicant
    if request.user.profile.role != 'APPLICANT':
        messages.error(request, 'Access denied. This dashboard is for job seekers only.')
        return redirect('users:home')
    
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
    if request.user.profile.role != 'RECRUITER':
        messages.error(request, 'Access denied. This dashboard is for recruiters only.')
        return redirect('users:home')
    
    # Get jobs posted by the user's company
    jobs = Job.objects.filter(company=request.user.profile.company)
    
    # Get active jobs count
    active_jobs_count = jobs.filter(is_active=True).count()
    
    # Get applications for the user's company's jobs
    applications = JobApplication.objects.filter(job__company=request.user.profile.company)
    
    # Get pending applications count
    pending_applications_count = applications.filter(status='PENDING').count()
    
    # Get upcoming interviews
    interviews = Interview.objects.filter(
        application__job__company=request.user.profile.company,
        scheduled_date__gte=timezone.now(),
        status='SCHEDULED'
    ).order_by('scheduled_date')
    
    # Get recent applications
    recent_applications = applications.order_by('-applied_date')[:5]
    
    context = {
        'jobs': jobs,
        'active_jobs_count': active_jobs_count,
        'applications': applications,
        'pending_applications_count': pending_applications_count,
        'interviews': interviews,
        'recent_applications': recent_applications,
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
    
    # Add other user information to each conversation
    conversations_with_other_user = []
    for conversation in conversations:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        conversations_with_other_user.append({
            'conversation': conversation,
            'other_user': other_user
        })
    
    context = {
        'conversations_with_other_user': conversations_with_other_user,
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

def search_users(request):
    """Search for users by username, name, or skills"""
    query = request.GET.get('q', '')
    
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(profile__skills__icontains=query)
        ).distinct()
    else:
        users = User.objects.none()
    
    context = {
        'users': users,
        'query': query
    }
    return render(request, 'users/search_users.html', context)

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
    
    return redirect('users:chatbot')

@login_required
def select_chatbot_conversation(request, conversation_id):
    conversation = get_object_or_404(ChatbotConversation, id=conversation_id, user=request.user)
    request.session['active_chatbot_conversation'] = conversation.id
    return redirect('users:chatbot')

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
    """Generate a response from the chatbot using OpenAI API"""
    import openai
    import os
    from django.conf import settings
    
    # Get OpenAI API key from environment variables
    api_key = os.environ.get('OPENAI_API_KEY')
    
    if not api_key:
        # Fallback to a default response if API key is not available
        return "I'm your AI resume assistant, but I'm currently experiencing some technical difficulties. Please try again later or contact support."
    
    # Set up OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Get user profile information to provide context
    profile = user.profile
    profile_info = {
        "has_resume": bool(profile.resume),
        "has_skills": bool(profile.skills),
        "has_experience": bool(profile.experience),
        "has_education": bool(profile.education),
        "role": profile.role
    }
    
    # Create system message with context
    system_message = f"""
    You are an AI resume and job search assistant for a job portal. 
    Your goal is to help users improve their resumes, prepare for interviews, and enhance their job search strategies.
    
    User profile information:
    - Has uploaded resume: {profile_info['has_resume']}
    - Has listed skills: {profile_info['has_skills']}
    - Has listed experience: {profile_info['has_experience']}
    - Has listed education: {profile_info['has_education']}
    - Role on platform: {profile_info['role']}
    
    Provide helpful, concise advice tailored to the user's needs. If they haven't completed their profile,
    encourage them to do so for better job matching.
    """
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract and return the response text
        return response.choices[0].message.content
        
    except Exception as e:
        # Log the error (in a real application)
        print(f"Error calling OpenAI API: {str(e)}")
        
        # Return a fallback response
        return """I apologize, but I'm having trouble connecting to my knowledge base right now. 
        
Here are some general tips that might help:
1. Tailor your resume to each job application
2. Quantify your achievements with numbers when possible
3. Prepare for interviews by researching the company
4. Network actively to find hidden job opportunities

Please try again later for more personalized assistance."""

@login_required
def logout_view(request):
    """
    Handle logout with confirmation page
    """
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('users:home')
    return render(request, 'users/logout.html')

def github_login(request):
    """
    Display the GitHub login page
    """
    return render(request, 'users/github_login.html')

