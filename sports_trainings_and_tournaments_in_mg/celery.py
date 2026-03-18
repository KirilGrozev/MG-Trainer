import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sports_trainings_and_tournaments_in_mg.settings")

app = Celery("sports_trainings_and_tournaments_in_mg")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
