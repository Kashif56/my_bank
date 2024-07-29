from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from allauth.account.decorators import verified_email_required
import random

from .models import BankAccount
# Create your views here.


def generate_account_number():
    remaining_digits = ''.join(random.choice('0123456789') for _ in range(12))
    credit_card_number = '1111' + remaining_digits
    return credit_card_number

@verified_email_required
@login_required
def open_bank_account(request):

    bank_account = BankAccount.objects.filter(user=request.user)
    if bank_account.exists():
        return redirect('core:dashboard')
    
    context = {}
    context['bank_account_created'] = False
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        profession = request.POST.get('profession')
        account_type = request.POST.get('account_type')
        address = request.POST.get('address')
        phone_number = request.POST.get('phone_number')
        account_number = generate_account_number()

        if account_type == 'Current' or 'Islamic':
            new_account = BankAccount(
                user = request.user,
                full_name = full_name,
                phone_number = phone_number,
                profession = profession,
                account_type = account_type,
                account_number=account_number,
                address=address,
            )
        
            new_account.save()
            messages.success(request, "Thank You for your Interest in Online Bank. Your request for Account opening has been received. Please wait for Approval.")
            
            return redirect('bankaccount:approve_bank_account', account_number)

    return render(request, 'open_bank_account.html', context)


@login_required
def approve_bank_account(request, account_number):
    context = {}
    bank_account = BankAccount.objects.get(account_number=account_number)
    context['item'] = bank_account

    if bank_account.is_approved == True:
        return redirect('core:dashboard')

    return render(request, 'account_approval.html', context)



@login_required
def bank_account_setting(request):
    context = {}
    context['bank_account_created'] = True
    return render(request, 'account_setting.html', context)



def user_profile(request, user):
    context = {}
    context['bank_account_created'] = True
    bank_account = BankAccount.objects.get(user=request.user)
    context['bank_account'] = bank_account
    
    
    return render(request, 'user_profile.html', context)