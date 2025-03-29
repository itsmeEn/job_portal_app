from django.urls import path
from . import views
from django.contrib.auth import views as auth_views # Import Django's built-in logout view

app_name = 'users'

urlpatterns = [
    # Home URL
    path('', views.home, name='home'),
    
    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('messages/', views.message_list, name='message_list'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start-conversation/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    path('search/', views.search_users, name='search_users'),

    # Authentication URLs
    path('applicant/login/', views.applicant_login, name='applicant_login'),
    path('recruiter/login/', views.recruiter_login, name='recruiter_login'),
    path('github/login/', views.github_login, name='github_login'),
    path('applicant/signup/', views.applicant_signup, name='applicant_signup'),
    path('recruiter/signup/', views.recruiter_signup, name='recruiter_signup'),

    # Dashboard URLs
    path('applicant/dashboard/', views.applicant_dashboard, name='applicant_dashboard'),
    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),

    # Chatbot URLs
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/new/', views.new_chatbot_conversation, name='new_chatbot_conversation'),
    path('chatbot/<int:conversation_id>/', views.select_chatbot_conversation, name='select_chatbot_conversation'),
    path('chatbot/send/', views.send_chatbot_message, name='send_chatbot_message'),

    # Logout URL
    path('logout/', views.logout_view, name='logout'),

    # Activation URL
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate'),
]