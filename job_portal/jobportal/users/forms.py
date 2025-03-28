from django import forms
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'profile_picture', 'resume', 'skills', 
            'experience', 'education', 'location', 'phone_number',
            'linkedin_profile', 'github_profile', 'website'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter skills separated by commas'}),
            'experience': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'education': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_profile': forms.URLInput(attrs={'class': 'form-control'}),
            'github_profile': forms.URLInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

class MessageForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Type your message here...'}),
        label=''
    )

class ChatbotMessageForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'class': 'form-control', 
            'placeholder': 'Ask me about resume help, interview tips, or job search advice...',
            'id': 'chatbot-message-input'
        }),
        label='',
        required=True
    )

class RecruiterSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'company_name', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

