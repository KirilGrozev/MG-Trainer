from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied

ALLOWED_DOMAIN = 'schoolmath.eu'


def allowed_email(email):
    return bool(email and email.lower().endswith(f'@{ALLOWED_DOMAIN}'))


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

    def clean_email(self, email):
        email = super().clean_email(email)
        if not allowed_email(email):
            raise PermissionDenied('Неразрешен домейн.')
        return email

    def authenticate(self, request, **credentials):
        user = super().authenticate(request, **credentials)
        if user and not allowed_email(getattr(user, 'email', None)):
            raise PermissionDenied('Неразрешен домейн.')
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        email = sociallogin.user.email or sociallogin.account.extra_data.get('email')
        return allowed_email(email)

    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email or sociallogin.account.extra_data.get('email')
        if not allowed_email(email):
            raise PermissionDenied('Неразрешен домейн.')
