from .models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):
    """
    Create user profile for social auth users if it doesn't exist
    """
    if not hasattr(user, 'profile'):
        profile = UserProfile.objects.create(
            user=user,
            role='APPLICANT'  # Default role for GitHub login
        )
        
        # If using GitHub, try to get additional information
        if backend.name == 'github':
            if response.get('name'):
                names = response['name'].split(' ', 1)
                user.first_name = names[0]
                if len(names) > 1:
                    user.last_name = names[1]
            
            if response.get('bio'):
                profile.bio = response['bio']
            
            if response.get('blog'):
                profile.website = response['blog']
            
            if response.get('location'):
                profile.location = response['location']
            
            # Save the profile and user
            profile.save()
            user.save()
    
    return {
        'user': user,
        'is_new': kwargs.get('is_new', False)
    } 