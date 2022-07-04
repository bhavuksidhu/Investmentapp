from django.db import models

class ContactData(models.Model):
    company_email = models.EmailField(null=True)
    company_number = models.CharField(max_length=20, unique=True, null=True)
    company_address = models.TextField()
    

# Create your models here.
class StaticData(models.Model):
    about_us = models.TextField()
    privacy_policy = models.TextField()
    terms_and_conditions = models.TextField() 
    contact_data = models.OneToOneField(ContactData,on_delete=models.SET_NULL,null=True)

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()