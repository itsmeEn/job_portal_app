from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_authenticated:
            if user.profile.role == 'APPLICANT':
                return reverse('users:applicant_dashboard')
            elif user.profile.role == 'RECRUITER':
                return reverse('users:recruiter_dashboard')
        return reverse('users:home')

    def get_signup_redirect_url(self, request):
        return self.get_login_redirect_url(request) 