from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomerSupport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    resolved_at = models.DateTimeField(null=True, blank=True)


class IssueResponse(models.Model):
    issue = models.ForeignKey(CustomerSupport, on_delete=models.CASCADE)
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)