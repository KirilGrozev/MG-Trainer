from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied

ALLOWED_DOMAIN = 'schoolmath.eu'


def allowed_email(email):
    return bool(email and email.lower().endswith(f'@{ALLOWED_DOMAIN}'))


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        email = sociallogin.user.email or sociallogin.account.extra_data.get('email')
        return allowed_email(email)

    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email or sociallogin.account.extra_data.get('email')
        if not allowed_email(email):
            raise PermissionDenied('Неразрешен домейн.')
