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
    first_name = models.CharField(default="", max_length=30)
    last_name = models.CharField(default="", max_length=30)
    date_of_birth = models.DateField(null=True)
    gender = models.CharField(max_length=7, choices=GENDER_CHOICES, null=True)
    pan_number = models.CharField(default="",max_length=12)
    address = models.TextField(default="")


class UserSetting(models.Model):
    DEVICE_TYPE_CHOICES = [("Apple", "Apple"), ("Android", "Android")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    notification_preference = models.BooleanField(default=True)
    device_token = models.CharField(default="", max_length=500, null=True, blank=True)
    device_type = models.CharField(
        default="", max_length=20, choices=DEVICE_TYPE_CHOICES
    )


class ZerodhaData(models.Model):
    local_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="zerodha_data"
    )
    user_type = models.CharField(default="individual", max_length=50, blank=True,null=True)
    email = models.EmailField(max_length=255, unique=True, null=True)
    user_name = models.CharField(default="", max_length=100, blank=True,null=True)
    user_shortname = models.CharField(default="", max_length=50, blank=True,null=True)
    broker = models.CharField(default="", max_length=30, blank=True,null=True)
    exchanges = ArrayField(models.CharField(max_length=10, blank=True),null=True)
    products = ArrayField(models.CharField(max_length=10, blank=True),null=True)
    order_types = ArrayField(models.CharField(max_length=10, blank=True),null=True)
    avatar_url = models.URLField()
    user_id = models.CharField(default="", max_length=20,null=True)
    api_key = models.CharField(default="", max_length=30,null=True)
    access_token = models.CharField(default="", max_length=100,null=True)
    public_token = models.CharField(default="", max_length=100,null=True)
    refresh_token = models.CharField(default="", max_length=100,null=True)
    enctoken = models.CharField(default="", max_length=100,null=True)
    login_time = models.DateTimeField(null=True)


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    NOTIFICATION_TYPES = [
        ("News", "News"),
        ("Stock-Listing", "Stock-Listing"),
        ("Others", "Others"),
    ]
    head = models.TextField()
    body = models.TextField()
    notification_type = models.CharField(
        default="", max_length=20, choices=NOTIFICATION_TYPES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
