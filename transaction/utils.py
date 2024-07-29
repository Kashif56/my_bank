from django.db.models import Q


import random
from datetime import date, timedelta, datetime


from .models import Card, Transaction
from bankaccount.models import BankAccount, Notifications






def generate_otp():
    return random.randint(100000, 999999)

def generate_otp_expiry():
    return datetime.now() + timedelta(minutes=5)  # OTP valid for 5 minutes




def generate_card_number():
    remaining_digits = ''.join(random.choice('0123456789') for _ in range(12))
    card_number = '4444' + remaining_digits
    return card_number

def card_expiry_date():
    today = date.today()
    expiry_date = today + timedelta(days=5*365)
    return expiry_date

def get_transactions_total(user):
    try:
        bank_account = BankAccount.objects.get(user=user)
        
        # Fetch transactions where the user's bank account is either sender or receiver
        transactions = Transaction.objects.filter(Q(from_acc=bank_account) | Q(to_acc=bank_account))
        
        credit_total = 0
        debit_total = 0
        
        for trx in transactions:
            if trx.from_acc == bank_account:
                # Transaction is a debit from the user's bank account
                debit_total += trx.amount
            elif trx.to_acc == bank_account:
                # Transaction is a credit to the user's bank account
                credit_total += trx.amount
        
        return credit_total, debit_total
    
    except BankAccount.DoesNotExist:
        # Handle case where the user's bank account does not exist
        return 0, 0
    except Exception as e:
        # Handle other exceptions gracefully
        print(f"An error occurred: {str(e)}")
        return 0, 0
    

def create_notification(user, content):
    notification = Notifications(user=user, content=content)
    notification.save()

