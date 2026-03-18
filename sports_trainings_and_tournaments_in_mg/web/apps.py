from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sports_trainings_and_tournaments_in_mg.web'

    def ready(self):
        import sports_trainings_and_tournaments_in_mg.web.signals
