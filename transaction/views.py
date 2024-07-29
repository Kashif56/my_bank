from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils import timezone
from allauth.account.decorators import verified_email_required
from django.contrib.admin.views.decorators import staff_member_required
import pandas as pd
import csv
from io import BytesIO

import random
from datetime import date, timedelta, datetime
from decimal import Decimal

from .models import Card, Transaction, RequestMoney
from bankaccount.models import BankAccount, Notifications
from .utils import generate_card_number, card_expiry_date, get_transactions_total, create_notification,                 generate_otp, generate_otp_expiry


MAX_OTP_ATTEMPTS = 5


def validate_transaction_limits(account, amount):
    return not any([
        amount > account.daily_remaining_limit,
        amount > account.monthly_remaining_limit,
        amount > account.yearly_remaining_limit
    ])



@verified_email_required
@login_required
def make_payment(request, account_number):
    context = {}
    req_id = request.GET.get('req_id')
   
    request_item = None
    if req_id:
        request_item = RequestMoney.objects.get(id=req_id)
        context['request_item'] = request_item
    
    user_account = BankAccount.objects.get(account_number=account_number)
    context['bank_account'] = user_account
    context['bank_account_created'] = True

   
    if request.method == 'POST':
        to_acc = request.POST.get('to_acc')
        amount = Decimal(request.POST.get('amount'))
        trx_type = 'Debit'
        trx_id = ''.join(random.choice('0123456789') for _ in range(6))


        if BankAccount.objects.filter(account_number=to_acc).exists():
            if user_account.balance >= amount:
                if validate_transaction_limits(user_account, amount):
                    target_account = BankAccount.objects.get(account_number=to_acc)
                    new_trx = Transaction(
                        from_acc=user_account,
                        to_acc = target_account,
                        amount=amount,
                        trx_type=trx_type,
                        trx_id=trx_id,
                    )

                    new_trx.save()

                    # Updating OTP to User Bank Account

                    user_account.otp = generate_otp()
                    user_account.otp_expiry = generate_otp_expiry()
                    user_account.save()

                    send_mail(
                        'Your OTP Code',
                        f'Your OTP code is {user_account.otp}. It is valid for 5 minutes.',
                        '8bpcoins4u@gmail.com',
                        [user_account.user.email],
                        fail_silently=False,
                    )

                    if request_item is not None:
                        url = reverse('transaction:trx_verify_otp', kwargs={'trx_id': trx_id})
                        query_params = f'?req_id={request_item.id}'
                        
                        return HttpResponseRedirect(url + query_params)
                    
                    else:
                        return redirect('transaction:trx_verify_otp', trx_id)

                  
                    
                else:
                    messages.error(request, "You have exceeded your Limits")
                    return redirect('transaction:make_payment', account_number)

            else:
                messages.error(request, "Insufficaint Balance")
                return redirect('transaction:make_payment', account_number)

        else:
            messages.error(request, "Bank Account with this Account Number Does not exists.")
            return redirect('transaction:make_payment', account_number)

    
    return render(request, "make_payment.html", context)


def otp_verified_transaction(request, trx_id):
    context = {}
    context['bank_account_created'] = True
    trx = Transaction.objects.get(trx_id=trx_id)
    context['item'] = trx
    fromAcc = trx.from_acc
    toAcc = trx.to_acc
    context['bank_account'] = fromAcc

    req_id = request.GET.get('req_id')
   
    request_item = None
    if req_id:
        request_item = RequestMoney.objects.get(id=req_id)
        context['request_item'] = request_item

    if request.method == 'POST':

        otp_code = request.POST.get('otp_code')
        
        if fromAcc.otp_attempts >= MAX_OTP_ATTEMPTS:
                messages.error(request, 'Maximum OTP attempts exceeded. Please request a new one.')
                fromAcc.otp = None
                fromAcc.otp_expiry = None
                fromAcc.save()

                trx.delete()
                return redirect('transaction:make_payment', fromAcc.account_number)
        
        if trx.initiate_trx == True:
            if fromAcc.otp_expiry > timezone.now():
                if fromAcc.otp == otp_code:

                    trx.is_otp_verified = True
                    trx.initiate_trx = False
                    trx.save()

                    fromAcc.otp = None
                    fromAcc.otp_expiry = None
                    fromAcc.save()
                    if request_item is not None:
                        request_item.is_accepted = True
                        request_item.transaction = trx
                        request_item.transaction_at = timezone.now()

                        request_item.save()

                        Notifications.objects.create(
                            user=request_item.request_from,
                            content = f"Your request to {request_item.request_to} is accepted and Transaction is made. TRX ID: {trx.trx_id}"
                        ) 

                    # Created Notification for User who transferred Payment
                    create_notification(fromAcc, f"You have transferred Rs. {trx.amount} to {toAcc} on {timezone.now()}")
                    
                    # Created Notification for User who Received Payment
                    create_notification(toAcc, f"You have received Rs. {trx.amount} from {fromAcc} at {timezone.now()}")

                    # Sending Email to From Account User
                    send_mail("Debit Payment", f"You have transfered Rs. {trx.amount} to {toAcc} on {timezone.now()}", '8bpcoins4u@gmail.com', [fromAcc.user.email,]) 

                    send_mail('Credit Payment',f"You have received Rs. {trx.amount} from {fromAcc} at {timezone.now()}", '8bpcoins4u@gmail.com', [toAcc.user.email,] )

                    return redirect('transaction:payment_successful', trx_id)
                
                else:
                    # Increment OTP attempts
                    fromAcc.otp_attempts += 1
                    fromAcc.save()
                    messages.error(request, 'Invalid OTP')
            else:
                messages.error(request,'OTP is Expired.')
            
        else:
            messages.error(request, "Transaction is Not Initiated")
            fromAcc.otp = None
            fromAcc.otp_expiry = None
            fromAcc.save()
            trx.delete()
            return redirect('transaction:make_payment', fromAcc.account_number)
    
    return render(request,'trx_otp_verify.html', context)


@login_required
def payment_successful(request, trx_id):
    context = {}
    context['bank_account_created'] = True
    trx = Transaction.objects.get(trx_id=trx_id)
    context['bank_account'] = trx.from_acc
    context['item'] = trx
    return render(request, 'payment_successful.html', context)

@verified_email_required
@login_required
def limit_management(request, account_number):
    context = {}
    bank_account = BankAccount.objects.get(account_number=account_number)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True
    if request.method == 'POST':
        monthly_limit = request.POST.get('monthly_limit')
        daily_limit = request.POST.get('daily_limit')
        yearly_limit = request.POST.get('yearly_limit')

        if monthly_limit and daily_limit and yearly_limit:
            try:
                # Calculate the difference between old and new limits
                daily_limit_diff = int(daily_limit) - bank_account.daily_limit
                monthly_limit_diff = int(monthly_limit) - bank_account.monthly_limit
                yearly_limit_diff = int(yearly_limit) - bank_account.yearly_limit

                # Update the limits
                bank_account.daily_limit = int(daily_limit)
                bank_account.monthly_limit = int(monthly_limit)
                bank_account.yearly_limit = int(yearly_limit)

                # Adjust the remaining limits
                bank_account.daily_remaining_limit += daily_limit_diff
                bank_account.monthly_remaining_limit += monthly_limit_diff
                bank_account.yearly_remaining_limit += yearly_limit_diff

                bank_account.date_updated = timezone.now()

                bank_account.save()

                messages.success(request, "Limit settings saved")
                return redirect('transaction:limit_management', bank_account.account_number)
            except ValueError:
                messages.error(request, "Invalid input. Please enter valid numbers for the limits.")
        else:
            messages.error(request, "All limit fields are required.")

    return render(request, 'limit_management.html', context)




    return render(request, 'limit_management.html', context)

@verified_email_required
@login_required
def apply_for_card(request, account_number):
    account = BankAccount.objects.get(account_number=account_number)

    if account.cards.filter(is_applied=True).exists():
        messages.success(request, "You already have applied for Debit Card. Please Wait for Approval. Thank You")
        return redirect('transaction:manage_card', account.account_number)
    
    card_number = generate_card_number()
    card_cvv = ''.join(random.choice('0123456789') for _ in range(3))
    card_expiry = card_expiry_date() 
    card_name = account.full_name

    new_card = Card(
        card_name = card_name,
        card_number = card_number,
        card_cvv = card_cvv,
        card_expiry = card_expiry,
        account = account,
        is_applied = True
    )

    new_card.save()
    
    messages.success(request, "Your request for Debit Card has been received. Please Wait for Approval. Thank You")


    create_notification(account, f"Your request for Debit Card has been received. Please Wait for Approval. on {timezone.now()}")


    return redirect('transaction:manage_card', account.account_number)
    
  
        

@verified_email_required
@login_required
def manage_card(request, account_number):
    context = {}
    try:
        bank_account = BankAccount.objects.get(account_number=account_number)
        card = Card.objects.get(account=bank_account)
        context['card'] = card
        context['bank_account'] = bank_account
        context['bank_account_created'] = True
        if request.method == 'POST':
            is_active = request.POST.get('is_active') == 'on'

            card.is_active = is_active
            card.save()
            
            messages.success(request, "Card Settings Saved")

            return redirect('transaction:manage_card', bank_account.account_number)


        return render(request, 'manage_card.html', context)
    
    except Card.DoesNotExist:
        messages.error(request, "You do not have an Debit Card Please Apply for it.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', 'core:dashboard'))




@login_required
def transaction_history(request, account_number):
    context = {}
    bank_account = BankAccount.objects.get(account_number=account_number)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True
    trx_history = Transaction.objects.filter(Q(from_acc=bank_account) | Q(to_acc=bank_account))
    context['trx_history'] = trx_history
    context['credit_total'] = get_transactions_total(request.user)[0]
    context['debit_total'] = get_transactions_total(request.user)[1]

    return render(request, 'transaction_history.html', context)



def request_money(request):
    context = {}
    request_from = BankAccount.objects.get(user=request.user)
    context['bank_account'] = request_from
    context['bank_account_created'] = True
    
    if request.method == 'POST':
        request_to_accountNo = request.POST.get('request_to')
        amount = int(request.POST.get('amount'))
        note = request.POST.get('note')

        if BankAccount.objects.filter(account_number=request_to_accountNo).exists():
            request_to = BankAccount.objects.filter(account_number=request_to_accountNo)[0]

            new_request = RequestMoney(
                request_from = request_from,
                request_to = request_to,
                amount = amount,
                note = note,
            )

            new_request.save()
            messages.success(request, "Your request has been Sent.")

            return redirect('transaction:request_money_detail', new_request.id)

        else:
            messages.error(request, "Account with this Account Number does not exists.")
            return redirect('transaction:request_money')

    return render(request, 'request_money.html', context)



def request_money_detail(request, id):
    context = {}
    bank_account = BankAccount.objects.get(user=request.user)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True

    money_request_item = RequestMoney.objects.get(id=id)
    context['item'] = money_request_item
    
    return render(request, 'request_money_detail.html', context)


def all_requests(request, account_number):
    context = {}
    bank_account = BankAccount.objects.get(account_number=account_number)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True

    requests_qs = RequestMoney.objects.filter(Q(request_from=bank_account) | Q(request_to=bank_account))
    context['requests_qs'] = requests_qs.order_by('is_accepted')
    
    return render(request, 'all_money_requests.html', context)

def accept_request(request, req_id):
    request_item = get_object_or_404(RequestMoney, id=req_id)

    account_number = request_item.request_to.account_number
    url = reverse('transaction:make_payment', kwargs={'account_number': account_number})
    query_params = f'?req_id={req_id}'
    
    return HttpResponseRedirect(url + query_params)


def reject_request(request, req_id):
    request_item = get_object_or_404(RequestMoney, id=req_id)
    request_item.is_rejected = True
    request_item.save()


    create_notification(request_item.request_from, f"Your request of to {request_item.request_to} for Rs {request_item.amount} has been rejected.")

    messages.success(request, "Request Rejected")    
    
    return redirect('transaction:all_requests', request_item.request_to.account_number)






        
    
# Generating Reports

def generate_yearly_trx_report(request):
    # Get the start and end of the current year
    now = timezone.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_year = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)

    # Fetch all bank accounts
    bank_accounts = BankAccount.objects.all()

    # Create empty lists to hold data for DataFrames
    credit_data = []
    debit_data = []

    # Iterate over each bank account and fetch transactions for the current year
    for bank_account in bank_accounts:
        transactions = Transaction.objects.filter(
            Q(from_acc=bank_account) | Q(to_acc=bank_account),
            timestamp__range=(start_of_year, end_of_year)
        ).order_by('-timestamp')

        for trx in transactions:
            trx_timestamp = trx.timestamp.astimezone(timezone.get_default_timezone()).replace(tzinfo=None)  # Make datetime naive

            if trx.from_acc == bank_account:
                # Debit transaction
                debit_data.append([
                    bank_account.account_number,
                    bank_account.full_name,
                    trx.trx_id,
                    'Debit',
                    trx.amount,
                    trx_timestamp,
                    trx.to_acc
                ])
            elif trx.to_acc == bank_account:
                # Credit transaction
                credit_data.append([
                    bank_account.account_number,
                    bank_account.full_name,
                    trx.trx_id,
                    'Credit',
                    trx.amount,
                    trx_timestamp,
                    trx.from_acc
                ])

    # Create DataFrames for Credit and Debit
    credit_df = pd.DataFrame(credit_data, columns=['Account Number', 'Account Holder', 'Transaction ID', 'Transaction Type', 'Amount', 'Timestamp', 'From'])
    debit_df = pd.DataFrame(debit_data, columns=['Account Number', 'Account Holder', 'Transaction ID', 'Transaction Type', 'Amount', 'Timestamp', 'To'])

    # Create an Excel writer object and add DataFrames as separate sheets
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        credit_df.to_excel(writer, sheet_name='Credit Transactions', index=False)
        debit_df.to_excel(writer, sheet_name='Debit Transactions', index=False)

    # Set the cursor to the beginning of the stream
    output.seek(0)

    filename = f'yearly_transaction_report_{now.strftime("%Y")}.xlsx'
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'


    return response

def generate_daily_trx_report(request):
    # Get the start and end of the current day
    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Fetch all bank accounts
    bank_accounts = BankAccount.objects.all()

    # Create empty lists to hold data for DataFrames
    credit_data = []
    debit_data = []

    # Iterate over each bank account and fetch transactions for the current day
    for bank_account in bank_accounts:
        transactions = Transaction.objects.filter(
            Q(from_acc=bank_account) | Q(to_acc=bank_account),
            timestamp__range=(start_of_day, end_of_day)
        ).order_by('-timestamp')

        for trx in transactions:
            trx_timestamp = trx.timestamp.astimezone(timezone.get_default_timezone()).replace(tzinfo=None)  # Make datetime naive

            if trx.from_acc == bank_account:
                # Debit transaction
                debit_data.append([
                    bank_account.account_number,
                    bank_account.full_name,
                    trx.trx_id,
                    'Debit',
                    trx.amount,
                    trx_timestamp,
                    trx.to_acc
                ])
            elif trx.to_acc == bank_account:
                # Credit transaction
                credit_data.append([
                    bank_account.account_number,
                    bank_account.full_name,
                    trx.trx_id,
                    'Credit',
                    trx.amount,
                    trx_timestamp,
                    trx.from_acc
                ])

    # Create DataFrames for Credit and Debit
    credit_df = pd.DataFrame(credit_data, columns=['Account Number', 'Account Holder', 'Transaction ID', 'Transaction Type', 'Amount', 'Timestamp', 'Related Account'])
    debit_df = pd.DataFrame(debit_data, columns=['Account Number', 'Account Holder', 'Transaction ID', 'Transaction Type', 'Amount', 'Timestamp', 'Related Account'])

    # Create an Excel writer object and add DataFrames as separate sheets
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        credit_df.to_excel(writer, sheet_name='Credit Transactions', index=False)
        debit_df.to_excel(writer, sheet_name='Debit Transactions', index=False)

    # Set the cursor to the beginning of the stream
    output.seek(0)

    filename = f'daily_transaction_report_{now.strftime("%Y-%m-%d")}.xlsx'
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def generate_monthly_trx_report(request):
    # Get the start and end of the current month
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_of_month = (start_of_month + pd.DateOffset(months=1)).replace(day=1, hour=23, minute=59, second=59, microsecond=999999) - pd.DateOffset(seconds=1)

    # Fetch all bank accounts
    bank_accounts = BankAccount.objects.all()

    # Create empty lists to hold data for DataFrames
    credit_data = []
    debit_data = []

    # Iterate over each bank account and fetch transactions for the current month
    for bank_account in bank_accounts:
        transactions = Transaction.objects.filter(
            Q(from_acc=bank_account) | Q(to_acc=bank_account),
            timestamp__range=(start_of_month, end_of_month)
        ).order_by('-timestamp')

        for trx in transactions:
            trx_timestamp = trx.timestamp.astimezone(timezone.get_default_timezone()).replace(tzinfo=None)  # Make datetime naive

            if trx.from_acc == bank_account:
                # Debit transaction
                debit_data.append([
                    bank_account.account_number,
                    bank_account.full_name,
                    trx.trx_id,
                    'Debit',
                    trx.amount,
                    trx_timestamp,
                    trx.to_acc
                ])
            elif trx.to_acc == bank_account:
                # Credit transaction
                credit_data.append([
                    bank_account.account_number,
                    bank_account.full_name,
                    trx.trx_id,
                    'Credit',
                    trx.amount,
                    trx_timestamp,
                    trx.from_acc
                ])

    # Create DataFrames for Credit and Debit
    credit_df = pd.DataFrame(credit_data, columns=['Account Number', 'Account Holder', 'Transaction ID', 'Transaction Type', 'Amount', 'Timestamp', 'Related Account'])
    debit_df = pd.DataFrame(debit_data, columns=['Account Number', 'Account Holder', 'Transaction ID', 'Transaction Type', 'Amount', 'Timestamp', 'Related Account'])

    # Create an Excel writer object and add DataFrames as separate sheets
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        credit_df.to_excel(writer, sheet_name='Credit Transactions', index=False)
        debit_df.to_excel(writer, sheet_name='Debit Transactions', index=False)

    # Set the cursor to the beginning of the stream
    output.seek(0)

    filename = f'monthly_transaction_report_{now.strftime("%Y-%m")}.xlsx'
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'


    return response