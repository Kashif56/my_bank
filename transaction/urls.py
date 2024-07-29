from django.urls import path

from . import views

app_name = 'transaction'
urlpatterns = [
    path('make-payment/<account_number>/', views.make_payment, name='make_payment'),
    path('make-payment/<trx_id>/verify-otp/', views.otp_verified_transaction, name='trx_verify_otp'),
    path('payment-successful/<trx_id>/', views.payment_successful, name='payment_successful'),
    path('apply-debitcard/<account_number>/', views.apply_for_card, name='apply_card'),
    path('manage-card/<account_number>/', views.manage_card, name='manage_card'),
    path('limit-management/<account_number>/', views.limit_management, name='limit_management'),
    path('transaction-history/<account_number>/', views.transaction_history, name='transaction_history'),

    path('request-money/', views.request_money, name='request_money'),
    path('request-money/<id>/detail/', views.request_money_detail, name='request_money_detail'),
    path('all-requests/<account_number>/', views.all_requests, name='all_requests'),
    path('all-requests/<req_id>/accept/', views.accept_request, name='accept_request'),
    path('all-requests/<req_id>/reject/', views.reject_request, name='reject_request'),

    path('generate_daily_trx_report/', views.generate_daily_trx_report, name='generate_daily_trx_report'),
    path('generate_monthly_trx_report/', views.generate_monthly_trx_report, name='generate_monthly_trx_report'),
    path('generate_yearly_trx_report/', views.generate_yearly_trx_report, name='generate_yearly_trx_report'),

  
]