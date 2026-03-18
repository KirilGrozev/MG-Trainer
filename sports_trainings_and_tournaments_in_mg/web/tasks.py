from celery import shared_task
from .services import promote_students_and_graduate, create_upcoming_event_notifications


@shared_task
def promote_students():
    promote_students_and_graduate()


@shared_task
def create_event_notifications():
    create_upcoming_event_notifications()
