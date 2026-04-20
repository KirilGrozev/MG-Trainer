from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied

ALLOWED_DOMAIN = 'schoolmath.eu'


class SchoolAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email
        domain = email.split('@')[-1]

        if domain not in ALLOWED_DOMAIN:
            raise PermissionDenied("Only school account allowed")

    def is_open_for_signup(self, request, sociallogin):
        return True


#class TestSchoolAccountAdapter(DefaultAccountAdapter):
#    def clean_email(self, email):
#        domain = email.split('@')[-1]
#        if domain not in ALLOWED_DOMAIN:
#            raise PermissionDenied('Only school account allowed')
#        return email
