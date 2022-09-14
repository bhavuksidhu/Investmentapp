from django.db import models
import uuid
from core.models import User

class ContactData(models.Model):
    company_email = models.EmailField(null=True)
    company_number = models.CharField(max_length=20, unique=True, null=True)
    company_address = models.TextField()
    website = models.TextField(default="")
    

# Create your models here.
class StaticData(models.Model):
    about_us = models.TextField()
    privacy_policy = models.TextField()
    terms_and_conditions = models.TextField() 
    contact_data = models.OneToOneField(ContactData,on_delete=models.SET_NULL,null=True)

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()

class AdminNotification(models.Model):
    NOTIFICATION_CHOICES = [("NEW_USER", "NEW_USER"), ("SUBSCRIPTION", "SUBSCRIPTION"),("TRADE", "TRADE")]
    notification_type = models.CharField(
        max_length=13, choices=NOTIFICATION_CHOICES, null=True
    )
    title = models.TextField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class PasswordReset(models.Model):
    uid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Tip(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']