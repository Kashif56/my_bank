from django.urls import path

from . import views

app_name = 'bankaccount'

urlpatterns = [
    path('open-bank-account/', views.open_bank_account, name='open_bank_account'),
    path('approve/<account_number>/', views.approve_bank_account, name='approve_bank_account'),
    path('bank-account-setting/', views.bank_account_setting, name='bank_account_setting'),
    path('user-profile/<user>/', views.user_profile, name='user_profile'),
]