
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class TransactionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transaction'

    def ready(self):
        from django.core.management import call_command
        try:
            call_command('schedule_jobs')
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
