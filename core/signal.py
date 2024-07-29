from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from bankaccount.models import Notifications
from .models import IssueResponse, CustomerSupport
from django.utils import timezone


@receiver(post_save, sender=IssueResponse)
def update_resolved_at_and_notify(sender, instance, created, **kwargs):
    if created:  # Ensure it's a new instance
        issue = instance.issue
        if issue.resolved_at is None:  # Update resolved_at only if it was not previously set
            issue.resolved_at = timezone.now()
            issue.save()

            # Send notification
            subject = 'Your Issue has been resolved'
            message = 'Congratulations! The issue you reported has been resolved.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [issue.user.email]  # Assuming CustomerSupport has a ForeignKey to User


            send_mail(subject, message, from_email, recipient_list)

               
      

               
     
