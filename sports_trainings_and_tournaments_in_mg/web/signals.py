from allauth.account.signals import user_signed_up
from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Profile, Grade, Match


@receiver(user_signed_up)
def create_profile(request, user, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=user)

    if "_" in user.email:
        profile.role = 'student'

        Grade.objects.get_or_create(profile=profile)
    else:
        profile.role = 'teacher'

        user.is_staff = True
        user.save()

    profile.save()
