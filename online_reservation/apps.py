from django.apps import AppConfig


class OnlineReservationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_reservation'

    def ready(self):
        import online_reservation.signals
