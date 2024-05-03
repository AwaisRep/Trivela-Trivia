from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailAuthBackend(ModelBackend):
    """
    Email Authentication Backend

    Allows a user to sign in using an email/password pair rather than
    a username/password pair.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)  # Assume 'username' is the email.
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None  # Return None if no user is found
        return None  # Return None if the password check fails