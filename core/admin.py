from django.contrib import admin

# Register your models here.
from .models import CustomerSupport, IssueResponse

@admin.register(CustomerSupport)
class CustomerSupportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'resolved_at' ,'timestamp')
   
    list_filter = ('timestamp',)

@admin.register(IssueResponse)
class IssueResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'issue','timestamp')
    list_filter = ('timestamp',)