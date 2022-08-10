import uuid
from datetime import date

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.contrib.postgres.fields import ArrayField
from django.db import models
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
    is_email_verified = models.BooleanField(default=False)
    firebase_token = models.TextField(default="", unique=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=True)

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
    pan_number = models.CharField(default="", max_length=12, unique=True)
    address = models.TextField(default="")

    @property
    def age(self):
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (today.timetuple()[1:3] < self.date_of_birth.timetuple()[1:3])
        )


class UserSetting(models.Model):
    DEVICE_TYPE_CHOICES = [("Apple", "Apple"), ("Android", "Android")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    notification_preference = models.BooleanField(default=True)
    show_after_trade_modal = models.BooleanField(default=True)
    device_token = models.CharField(default="", max_length=500, null=True, blank=True)
    device_type = models.CharField(
        default="", max_length=20, choices=DEVICE_TYPE_CHOICES
    )


class UserSubscription(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="subscription"
    )
    active = models.BooleanField(default=False)
    date_from = models.DateTimeField(null=True)
    date_to = models.DateTimeField(null=True)

    @property
    def amount(self):
        if self.date_to and self.date_from:
            return ((self.date_to - self.date_from).days / 365) * 39
        else:
            return 0

    @property
    def total_amount(self):
        amount = self.amount
        return ((amount / 100) * 18) + amount


class UserSubscriptionHistory(models.Model):
    subscription = models.ForeignKey(
        UserSubscription, on_delete=models.CASCADE, related_name="history"
    )
    amount = models.FloatField()
    transaction_id = models.TextField()
    payment_gateway = models.TextField()
    notes = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ZerodhaData(models.Model):
    local_user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="zerodha_data"
    )
    user_type = models.CharField(
        default="individual", max_length=50, blank=True, null=True
    )
    email = models.EmailField(max_length=255, null=True)
    user_name = models.CharField(default="", max_length=100, blank=True, null=True)
    user_shortname = models.CharField(default="", max_length=50, blank=True, null=True)
    broker = models.CharField(default="", max_length=30, blank=True, null=True)
    exchanges = ArrayField(models.CharField(max_length=10, blank=True), null=True)
    products = ArrayField(models.CharField(max_length=10, blank=True), null=True)
    order_types = ArrayField(models.CharField(max_length=10, blank=True), null=True)
    avatar_url = models.URLField(null=True)
    user_id = models.CharField(default="", max_length=20, null=True)
    api_key = models.CharField(default="", max_length=30, null=True)
    access_token = models.TextField(default="", null=True)
    public_token = models.TextField(default="", null=True)
    refresh_token = models.TextField(default="", null=True)
    enctoken = models.TextField(default="", null=True)
    login_time = models.DateTimeField(null=True)
    meta = models.JSONField(null=True)
    funds = models.FloatField(default=0)


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


class Transaction(models.Model):
    TRANSACTION_CHOICES = [("BUY", "BUY"), ("SELL", "SELL")]
    uid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    trading_symbol = models.CharField(max_length=20, default="")
    exchange = models.CharField(max_length=10, default="")
    price = models.FloatField(null=True)
    quantity = models.IntegerField()
    amount = models.FloatField(null=True)
    transaction_type = models.CharField(
        max_length=5, choices=TRANSACTION_CHOICES, null=True
    )
    order_type = models.TextField(default="MARKET")
    if_not_invest_then_what = models.TextField(default="",null=True,blank=True)
    verified = models.BooleanField(default=False)
    status = models.TextField(default="Pending")
    executed = models.BooleanField(
        default=False
    )  # Used to check if we executed this trade on our end or not! (One trade should only open one time.)

    zerodha_postback = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def purchased_value(self):
        return self.amount

    class Meta:
        ordering = ["-created_at"]

class InvestmentInsight(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="insights"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    value = models.FloatField()
    
    class Meta:
        ordering = ["created_at"]


class Stock(models.Model):
    exchange = models.TextField()
    symbol = models.TextField()
    series = models.TextField(default="", null="")
    index_listing = models.TextField(default="", null="")


class MarketQuote(models.Model):
    company_name = models.TextField(null=True, default="")
    instrument_token = models.TextField()
    trading_symbol = models.TextField()
    price = models.FloatField()
    exchange = models.TextField()
    change = models.FloatField(null=True)

class EmailVerificationRecord(models.Model):
    uid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)