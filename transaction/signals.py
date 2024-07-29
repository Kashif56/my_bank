# transaction/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def start_scheduler(sender, **kwargs):
    if sender.name == 'transaction':
        try:
            call_command('schedule_jobs')
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
