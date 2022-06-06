from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
from rest_framework_simplejwt.tokens import RefreshToken


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp)
        )


def get_access_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)
