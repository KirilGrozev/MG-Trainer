from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import Profile, Event, Notification

FINAL_GRADE = 13


@transaction.atomic
def promote_students_and_graduate():
    today = timezone.now().date()
    curr_year = today.year

    if 10 < today.month < 7:
        return

    students = Profile.objects.filter(
        role='student',
        is_active=True
    ).select_related('grade')

    for profile in students:
        grade_obj = getattr(profile, 'grade', None)

        if not grade_obj:
            continue

        if grade_obj.last_promoted_year == curr_year:
            continue

        current_grade = grade_obj.grade

        if current_grade >= FINAL_GRADE:
            grade_obj.last_promoted_year = curr_year
            grade_obj.save(update_fields=['last_promoted_year'])
            continue

        if current_grade == 12:
            grade_obj.grade = FINAL_GRADE
            grade_obj.last_promoted_year = curr_year
            profile.is_active = False

            profile.save(update_fields=['is_active'])
            grade_obj.save(update_fields=['grade', 'last_promoted_year'])
            continue

        grade_obj.grade += 1
        grade_obj.last_promoted_year = curr_year
        grade_obj.save(update_fields=['grade', 'last_promoted_year'])


def create_upcoming_event_notifications(profile):
    if not profile.is_active or profile.is_banned_from_participation:
        return

    today = timezone.now().date()
    upcoming_limit = today + timedelta(days=3)

    events = (
        Event.objects.filter(
            date__gte=today,
            date__lte=upcoming_limit,
            is_active=True,
            activities__matches__teams__students=profile,
        )
        .distinct()
    )

    for event in events:
        Notification.objects.get_or_create(
            profile=profile,
            event=event,
            defaults={
                'title': f'Предстоящо събитие: {event.name}',
                'message': f'Участваш в {event.name}, което ще се проведе на {event.date}.',
            },
        )
