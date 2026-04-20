from django.contrib.auth import user_logged_in
from django.dispatch import receiver
from .models import Profile, Grade
from .services import create_upcoming_event_notifications, promote_students_and_graduate


@receiver(user_logged_in)
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


@receiver(user_logged_in)
def create_notifications_on_log_in(sender, request, user, **kwargs):
    profile = user.profile

    if profile.role == 'student' and profile.is_active:
        create_upcoming_event_notifications(profile)


@receiver(user_logged_in)
def promote_students_graduate_on_log_in(sender, request, user, **kwargs):
    profile = user.profile

    if profile.role == 'teacher':
        promote_students_and_graduate()
