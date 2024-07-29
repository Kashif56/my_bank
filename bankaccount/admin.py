# admin.py

from django.contrib import admin
from .models import  BankAccount, Notifications

class BankAccountAdmin(admin.ModelAdmin):
    change_list_template = 'custom-admin/change_list.html'

admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(Notifications)
