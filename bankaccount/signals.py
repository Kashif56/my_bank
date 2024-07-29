# signals.py

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import BankAccount, Notifications



@receiver(pre_save, sender=BankAccount)
def store_previous_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._pre_save_instance = BankAccount.objects.get(pk=instance.pk)
        except BankAccount.DoesNotExist:
            instance._pre_save_instance = None
    else:
        instance._pre_save_instance = None

@receiver(post_save, sender=BankAccount)
def send_account_approval_email(sender, instance, created, **kwargs):
   
    if not created:  # Ensure it's not a new instance
        previous_instance = getattr(instance, '_pre_save_instance', None)
        if previous_instance:
          
            if previous_instance.is_approved == False and instance.is_approved == True:
                subject = 'Your bank account has been approved'
                message = 'Congratulations! Your bank account has been approved. You can now access your account.'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [instance.user.email]  # Assuming BankAccount has a ForeignKey to User

                new_notification = Notifications(
                    user=instance,
                    content=message,
                )
                new_notification.save()
             

                send_mail(subject, message, from_email, recipient_list)
               
      
@receiver(post_save, sender=BankAccount)
def send_account_activated_email(sender, instance, created, **kwargs):
  
    if not created:  # Ensure it's not a new instance
        previous_instance = getattr(instance, '_pre_save_instance', None)
        if previous_instance:
           
            if previous_instance.is_active == False and instance.is_active == True:
                subject = 'Congrats! Your bank account is Active!'
                message = 'Congratulations! Your bank account is Active Now. You can now access your Bank Account.'
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [instance.user.email]  # Assuming BankAccount has a ForeignKey to User

                new_notification = Notifications(
                    user=instance,
                    content=message,
                )
                new_notification.save()
              

                send_mail(subject, message, from_email, recipient_list)
               
     
