from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class TransactionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transaction'

    def ready(self):
        import transaction.signals  # Import signals to connect them
