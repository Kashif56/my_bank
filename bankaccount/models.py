from django.db import models
from django.contrib.auth.models import User




ACCOUNT_CHOICES = [
    ('Current', 'Current'),
    ('Islamic', 'Islamic'),
]


class BankAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=16)
    profession = models.CharField(max_length=20)
    
    account_number = models.CharField(max_length=16)
    account_type = models.CharField(max_length=50, choices=ACCOUNT_CHOICES)
    balance = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    
    date_created = models.DateTimeField(auto_now=True)
    date_updated = models.DateTimeField(null=True, blank=True)
    
    daily_limit = models.IntegerField(default=25000)
    daily_remaining_limit = models.IntegerField(default=25000)
    max_daily_limit = models.IntegerField(default=50000)

    monthly_limit = models.IntegerField(default=500000)
    monthly_remaining_limit = models.IntegerField(default=500000)
    max_monthly_limit = models.IntegerField(default=750000)

    yearly_limit = models.IntegerField(default=1000000)
    yearly_remaining_limit = models.IntegerField(default=1000000)
    max_yearly_limit = models.IntegerField(default=1250000)


    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expiry = models.DateTimeField(null=True, blank=True)
    otp_attempts = models.PositiveIntegerField(default=0)


    def __str__(self) -> str:
        return f'{self.user.username} - {self.account_number}'
    
   



class Notifications(models.Model):
    user = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='notifications')
    content = models.CharField(max_length=500)  # Fixed typo
    timestamp = models.DateTimeField(auto_now=True)
    is_seen = models.BooleanField(default=False)

    def __str__(self):
        return str(self.user)