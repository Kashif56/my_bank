from django.apps import AppConfig


class BankaccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bankaccount'

    def ready(self):
        import bankaccount.signals  # Import the signals module