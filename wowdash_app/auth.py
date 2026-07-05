from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib import messages

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            # Check if the user exists
            user = UserModel.objects.get(Q(username=username) | Q(email=username))
            
            # First check if the user's profile is active
            if not user.profile.is_active:
                if request:
                    messages.error(request, "Your account has been deactivated. Please contact the administrator.")
                return None
                
            # Then check if the user is active in Django's auth system
            if not user.is_active:
                if request:
                    messages.error(request, "Your account has been disabled. Please contact the administrator.")
                return None
                
            # Finally check the password
            if user.check_password(password):
                return user
                
        except UserModel.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(pk=user_id)
            # Check both active statuses when retrieving the user
            if user.is_active and user.profile.is_active:
                return user
            return None
        except UserModel.DoesNotExist:
            return None 