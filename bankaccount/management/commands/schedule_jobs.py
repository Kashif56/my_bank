from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore, register_events
from apscheduler.schedulers.background import BackgroundScheduler
from transaction import tasks  # import your tasks module

class Command(BaseCommand):
    help = "Runs APScheduler as a Django management command."

    def handle(self, *args, **kwargs):
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Add your jobs here
        scheduler.add_job(tasks.reset_daily_limits_job, "interval", hours=24, id="reset_daily_limits_job", replace_existing=True)
        scheduler.add_job(tasks.reset_monthly_limits_job, "cron", day="1", hour="0", id="reset_monthly_limits_job", replace_existing=True)
        scheduler.add_job(tasks.reset_yearly_limits_job, "cron", month="1", day="1", hour="0", id="reset_yearly_limits_job", replace_existing=True)
        
        register_events(scheduler)
        scheduler.start()

        self.stdout.write("Scheduler started successfully.")
