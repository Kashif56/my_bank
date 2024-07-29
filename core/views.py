from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.cache import cache
import csv

from django.http import HttpResponse
from bankaccount.models import BankAccount, Notifications
from transaction.models import Transaction, Card
from transaction.views import get_transactions_total
from .models import CustomerSupport, IssueResponse
from transaction.views import get_transactions_total

# Create your views here.



@login_required
def dashboard(request):
    context = {}
    user = request.user
    context['bank_account_created'] = True
    
    if user.bankaccount_set.exists():
        # Using select_related to fetch related user in a single query
        bank_account = BankAccount.objects.select_related('user').get(user=user)

        if bank_account.is_approved and bank_account.is_active:
            # Using a cache to store transaction history
            trx_history = cache.get(f'{user.id}_trx_history')
            if trx_history is None:
                trx_history = Transaction.objects.all()
                cache.set(f'{user.id}_trx_history', trx_history, 60*5)  # Cache for 5 minutes
            
            context['bank_account'] = bank_account
            context['trx_qs'] = trx_history

            if bank_account.cards.filter(is_applied=True).exists():
                context['is_applied'] = True

            # Cache transaction totals
            credit_total = cache.get(f'{user.id}_credit_total')
            debit_total = cache.get(f'{user.id}_debit_total')
            if credit_total is None or debit_total is None:
                credit_total, debit_total = get_transactions_total(user)
                cache.set(f'{user.id}_credit_total', credit_total, 60*5)
                cache.set(f'{user.id}_debit_total', debit_total, 60*5)
            
            context['credit_total'] = credit_total
            context['debit_total'] = debit_total

            return render(request, 'dashboard.html', context)
        else:
            return redirect('bankaccount:approve_bank_account', bank_account.account_number)
    else:
        return redirect('bankaccount:open_bank_account')

    

def notifications(request, account_number):
    context = {}
    context['bank_account_created'] = True
    
    bank_account = BankAccount.objects.get(account_number=account_number)
    context['bank_account'] = bank_account
    
    notifications_qs = bank_account.notifications.all()
    context['qs'] = notifications_qs.order_by('-id')

    return render(request, 'notifications.html', context)



# Customer Support

def customer_support(request):
    context = {}
    
    bank_account = BankAccount.objects.get(user=request.user)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True

    issues_qs = CustomerSupport.objects.filter(user=request.user)

    context['issues'] = issues_qs
    
    return render(request, 'customer_support/all_issues.html', context)



def customer_support_detail(request, id):
    context = {}
    
    bank_account = BankAccount.objects.get(user=request.user)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True

    issue_item = CustomerSupport.objects.get(id=id)
   
    context['item'] = issue_item
    responses = issue_item.issueresponse_set.all()
    if responses:
        response = responses[0]
        context['response'] = response
    
    return render(request, 'customer_support/issue_detail.html', context)




def customer_support_form(request):
    context = {}
    
    bank_account = BankAccount.objects.get(user=request.user)
    context['bank_account'] = bank_account
    context['bank_account_created'] = True

    if request.method == 'POST':
        content = request.POST.get('content')
        user = request.user
        timestamp = timezone.now()

        new_issue = CustomerSupport(
            user=user,
            content=content,
            timestamp=timestamp
        )
        new_issue.save()

        messages.success(request, "Your Issue has been reported. It will be resolved within 24 hours.")
        return redirect('core:all_issues')
    
    return render(request, 'customer_support/form.html', context)


@staff_member_required
def generate_monthly_report(request):
    # Get the current month and year
    now = timezone.now()
    current_month = now.month
    current_year = now.year

    # Filter bank accounts created in the current month
    bank_accounts = BankAccount.objects.filter(date_created__year=current_year, date_created__month=current_month)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bank_accounts_report_{current_year}_{current_month}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Account Holder', 'Account Number', 'Address', 'Profession', 'Phone Number', 'Balance', 'Created At'])

    for account in bank_accounts:
        writer.writerow([
            account.full_name, 
            f"'{account.account_number}'",  # Encapsulate account number in double quotes
            account.address,
            account.profession,
            str(account.phone_number),
            account.balance,
            account.date_created
        ])

    return response



@staff_member_required
def generate_yearly_report(request):
    # Get the current month and year
    now = timezone.now()
    current_year = now.year

    # Filter bank accounts created in the current month
    bank_accounts = BankAccount.objects.filter(date_created__year=current_year)

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="bank_accounts_report_{current_year}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Account Holder', 'Account Number', 'Address', 'Profession', 'Phone Number', 'Balance', 'Created At'])

    for account in bank_accounts:
        writer.writerow([
            account.full_name, 
            f"'{account.account_number}'", 
            account.address,
            account.profession,
            str(account.phone_number),
            account.balance,
            account.date_created
        ])

    return response