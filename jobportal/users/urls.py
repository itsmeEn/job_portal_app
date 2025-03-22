from django.urls import path
from . import views
from .views import some_view


urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('messages/', views.message_list, name='message_list'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start-conversation/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    path('navbar/', some_view, name='navbar'),

]

