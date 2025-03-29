from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.http import HttpResponseRedirect

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # Check user role and redirect accordingly
        if request.user.profile.role == 'APPLICANT':
            return reverse('applicant_dashboard')
        elif request.user.profile.role == 'RECRUITER':
            return reverse('recruiter_dashboard')
        else:
            # If no role, redirect to home
            return reverse('home')

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_connect_redirect_url(self, request, socialaccount):
        return reverse('home')
    
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Social login users will need to sign up through regular forms
        # to get assigned a specific role
        return user

