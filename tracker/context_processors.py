from .models import UserAccessProfile

def auth_user_profile(request):
    """Provides user_profile and permission flags to all templates."""
    if hasattr(request, 'user') and request.user.is_authenticated:
        profile = UserAccessProfile.get_or_create_for_user(request.user)
        return {
            'user_profile': profile,
            'is_admin': profile.is_admin or request.user.is_superuser,
        }
    return {
        'user_profile': None,
        'is_admin': False,
    }
