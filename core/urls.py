from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('notifications/<account_number>/', views.notifications , name='notifications'),

    path('customer-support/', views.customer_support, name='all_issues'),
    path('customer-support/issue/<id>/detail', views.customer_support_detail, name='issue_detail'),
    path('customer-support/form/', views.customer_support_form, name='form'),

    path('bankaccount/monthly-reports/', views.generate_monthly_report,  name='bankaccount_monthly_reports'),
    path('bankaccount/yearly-reports/', views.generate_yearly_report,  name='bankaccount_yearly_reports'),
]