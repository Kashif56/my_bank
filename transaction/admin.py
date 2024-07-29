from django.contrib import admin
from .models import Transaction, Card, RequestMoney

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('trx_id', 'from_acc', 'to_acc', 'amount', 'trx_type', 'timestamp')
    search_fields = ('trx_id', 'from_acc__account_number', 'to_acc__account_number')
    list_filter = ('trx_type', 'timestamp')
    change_list_template = 'custom-admin/change_list_trx.html'

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('account', 'card_number', 'card_cvv', 'card_expiry', 'card_name', 'is_active', 'is_reviewed')
    search_fields = ('card_number', 'card_name', 'account__account_number')
    list_filter = ('is_active', 'is_reviewed')


@admin.register(RequestMoney)
class RequestMoneyAdmin(admin.ModelAdmin):
    list_display = ('request_from', 'request_to', 'amount', 'is_accepted')
    list_filter = ('is_accepted', 'requested_at',)