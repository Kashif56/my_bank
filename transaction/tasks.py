# transaction/tasks.py
import logging
from django.utils import timezone
from bankaccount.models import BankAccount
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job


scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

logger = logging.getLogger(__name__)
@register_job(scheduler, "interval", hours=24, replace_existing=True)
def reset_daily_limits_job():
    """
    Job to reset daily limits for all bank accounts.
    """
    accounts = BankAccount.objects.all()
    for account in accounts:
        account.daily_remaining_limit = account.daily_limit
        account.save()
    logger.info(f"Daily limits reset at {timezone.now()}")


@register_job(scheduler, "cron", day="1", hour="0", replace_existing=True)
def reset_monthly_limits_job():
    """
    Job to reset monthly limits for all bank accounts on the 1st day of every month at midnight.
    """
    accounts = BankAccount.objects.all()
    for account in accounts:
        account.monthly_remaining_limit = account.monthly_limit
        account.save()
    logger.info(f"Monthly limits reset at {timezone.now()}")


@register_job(scheduler, "cron", month="1", day="1", hour="0", replace_existing=True)
def reset_yearly_limits_job():
    """
    Job to reset yearly limits for all bank accounts on January 1st at midnight.
    """
    accounts = BankAccount.objects.all()
    for account in accounts:
        account.yearly_remaining_limit = account.yearly_limit
        account.save()
    logger.info(f"Yearly limits reset at {timezone.now()}")





# This function starts the scheduler when Django starts
def start_scheduler():
    scheduler.start()
    register_events(scheduler)
