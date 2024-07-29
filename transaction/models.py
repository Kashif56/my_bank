from typing import Iterable
from django.db import models
from django.db import models, transaction as db_transaction
from django.core.exceptions import ValidationError

from django.utils import timezone

from bankaccount.models import BankAccount

TRX_CHOICES = [
    ('Debit', 'Debit'),
    ('Credit', 'Credit'),
]


def validate_transaction_limits(account, amount):
    return not any([
        amount > account.daily_remaining_limit,
        amount > account.monthly_remaining_limit,
        amount > account.yearly_remaining_limit
    ])



class Transaction(models.Model):
    from_acc = models.ForeignKey('bankaccount.BankAccount', on_delete=models.DO_NOTHING, related_name='transactions_from')
    to_acc = models.ForeignKey('bankaccount.BankAccount', on_delete=models.DO_NOTHING, related_name='transactions_to')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    trx_type = models.CharField(max_length=10, choices=TRX_CHOICES)
    trx_id = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now=True)

    # Added to Procees trx if its otp verified
    is_otp_verified = models.BooleanField(default=False)
    initiate_trx = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.trx_id
    

    def save(self, *args, **kwargs):
        if self.from_acc.balance < self.amount:
            raise ValidationError('Insufficient balance in the source account.')

        with db_transaction.atomic():
            if self.is_otp_verified:
                # Updating Balance
                self.from_acc.balance -= self.amount
                self.to_acc.balance += self.amount

                # Updating Limits
                self.from_acc.daily_remaining_limit -= self.amount
                self.from_acc.monthly_remaining_limit -= self.amount
                self.from_acc.yearly_remaining_limit -= self.amount

            self.from_acc.save()
            self.to_acc.save()
            
            super(Transaction, self).save(*args, **kwargs)


    






class Card(models.Model):
    account = models.ForeignKey('bankaccount.BankAccount', on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=16)
    card_cvv = models.CharField(max_length=3)
    card_expiry = models.DateField()
    card_name = models.CharField(max_length=20)

    is_active = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    is_applied = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.card_number


class RequestMoney(models.Model):
    request_from = models.ForeignKey('bankaccount.BankAccount', on_delete=models.CASCADE, related_name='request_from')
    request_to = models.ForeignKey('bankaccount.BankAccount', on_delete=models.CASCADE, related_name='request_to')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField()

    requested_at = models.DateTimeField(default=timezone.now)
    
    is_accepted = models.BooleanField(default=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, blank=True, null=True)
    transaction_at = models.DateTimeField(null=True, blank=True) 

    is_rejected = models.BooleanField(default=False)


    def __str__(self) -> str:
        return str(self.id)