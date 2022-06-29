from datetime import datetime

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
# Create your models here.

class UploadedFile(models.Model):
    file = models.FileField(max_length=200)
    thumbnail = ImageSpecField(
        source="file",
        processors=[ResizeToFill(500, 500)],
        format="JPEG",
        options={"quality": 60},
    )
    created_at = models.DateTimeField(auto_now_add=True)

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        """Creates and saves a new user"""
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """Creates and saves a new super user"""
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=255, unique=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    zerodha_token = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        return f"{self.email}, {self.phone_number}"

    class Meta:
        ordering = ("-created_at",)

class UserProfile(models.Model):
    GENDER_CHOICES = [("Male", "Male"), ("Female", "Female"), ("Other", "Other")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_photo = models.OneToOneField(
        UploadedFile, on_delete=models.SET_NULL, null=True, related_name="profile"
    )
    age = models.IntegerField(default=0)
    gender = models.CharField(max_length=7, choices=GENDER_CHOICES, null=True)
    first_name = models.CharField(default="", max_length=30)
    last_name = models.CharField(default="", max_length=30)

class UserSetting(models.Model):
    DEVICE_TYPE_CHOICES = [("Apple","Apple"),("Android","Android")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    notification_preference = models.BooleanField(default=True)
    device_token = models.CharField(default="", max_length=500, null=True, blank=True)
    device_type = models.CharField(default="", max_length=20, choices=DEVICE_TYPE_CHOICES)

class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    head = models.TextField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]