from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone

from .models import Profile, Event, Notification
from django.contrib.auth import get_user_model

FINAL_GRADE = 13


@transaction.atomic
def promote_students_and_graduate():
    user = get_user_model()

    qs = (
        Profile.objects.select_for_update()
        .select_related('user')
        .filter(role='student')
        .exclude(grade__isnull=True)
    )

    qs.filter(grade__lt=FINAL_GRADE - 1).update(grade=models.F('grade') + 1)

    graduating = qs.filter(grade__gte=FINAL_GRADE - 1)

    graduating_user_ids = list(graduating.values_list('user_id', flat=True))

    user.profile.objects.filter(id__in=graduating_user_ids).update(is_active=False)


@transaction.atomic
def create_upcoming_event_notifications():
    today = timezone.now().date()
    upcoming_limit = today + timedelta(days=3)

    upcoming_events = Event.objects.filter(
        date__gte=today,
        date__lte=upcoming_limit,
        is_active=True,
    ).distinct()

    for event in upcoming_events:
        students = Profile.objects.filter(
            teamprofile__team__matches__activity__events=event,
            role='student',
            is_active=True,
            is_banned_from_participation=False,
        ).distinct()

        for student in students:
            Notification.objects.get_or_create(
                profile=student,
                event=event,
                title=f'Upcoming event: {event.name}',
                message=f'You are participating in {event.name} on {event.date}.',
            )
