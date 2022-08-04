from operator import mod
from pyexpat import model
import re
from mimetypes import guess_type

from attr import fields

from adminpanel.models import FAQ, ContactData, StaticData
from core.models import (
    InvestmentInsight,
    MarketQuote,
    Notification,
    Transaction,
    UploadedFile,
    User,
    UserProfile,
    UserSetting,
    UserSubscriptionHistory,
    UserSubscription,
    ZerodhaData,
)
from drf_spectacular.utils import extend_schema_serializer
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from .utils import PAN_REGEX

## UserSerializers


@extend_schema_serializer(many=False)
class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = "__all__"
        extra_kwargs = {"file": {"required": True, "use_url": True}}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.file:
            data["content-type"] = guess_type(instance.file.name)[0]
            if data["content-type"]:
                if "video" not in data["content-type"]:
                    data["thumbnail"] = instance.thumbnail.url
        return data

    def create(self, validated_data):
        request = self.context.get("request", None)
        profile_photo = super().create(validated_data)
        profile = request.user.profile
        profile.profile_photo = profile_photo
        profile.save()
        return profile_photo


class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = ["notification_preference", "device_token", "device_type"]

class BasicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email","is_email_verified","phone_number"]
        read_only_fields = ["is_email_verified"]
    
    def update(self, instance, validated_data):
        old_email = instance.email
        new_email = validated_data["email"]
        instance =  super().update(instance, validated_data)
        if old_email != new_email:
            instance.is_email_verified = False
            instance.save()
        return instance
        

@extend_schema_serializer(many=False)
class UserProfileSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    profile_photo = UploadedFileSerializer(allow_null=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "profile_photo",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "pan_number",
            "address",
        ]

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request:
            validated_data["user"] = request.user
        return super().create(validated_data)


@extend_schema_serializer(many=False)
class UserSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSetting
        fields = ["notification_preference", "device_token", "device_type"]

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request:
            validated_data["user"] = request.user
        return super().create(validated_data)

@extend_schema_serializer(many=False)
class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscription
        fields = ["active", "date_from", "date_to"]

class UserSubscriptionHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSubscriptionHistory
        fields = ["amount","transaction_id","payment_gateway","notes","created_at"]
    
    def validate(self, attrs):
        validated_data = super().validate(attrs)
        if validated_data["amount"] < 0:
            raise serializers.ValidationError(
                "Amount needs to be positive!"
            )
        subscription_id = self.context["request"].user.subscription.id
        validated_data["subscription_id"] = subscription_id
        return validated_data

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    settings = UserSettingSerializer()

    class Meta:
        model = User
        fields = [
            "email",
            "phone_number",
            "is_active",
            "profile",
            "settings",
        ]
        
@extend_schema_serializer(many=False)
class FundsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZerodhaData
        fields =["funds",]

class MarketQuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketQuote
        fields = ["company_name","trading_symbol","price","exchange","change"]

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["trading_symbol","exchange","quantity","transaction_type","if_not_invest_then_what"]

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id","trading_symbol","exchange","quantity","status","price","amount","transaction_type","if_not_invest_then_what","created_at"]

class TransactionGroupedByDateSerializer(serializers.Serializer):
    date = serializers.DateField()
    transactions = TransactionSerializer(many=True)

class PortfolioTransactionSerializer(serializers.Serializer):
    trading_symbol = serializers.CharField()
    exchange = serializers.CharField()
    quantity = serializers.IntegerField()
    purchased_value = serializers.FloatField()
    current_value = serializers.FloatField()

class PortfolioSerializer(serializers.Serializer):
    portfolio_list = PortfolioTransactionSerializer(many=True)
    num_of_transactions = serializers.IntegerField()
    total_purchase_value = serializers.FloatField()
    total_current_value = serializers.FloatField()

class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["transaction_type","amount","if_not_invest_then_what","created_at"]

class InsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentInsight
        fields = ["value","created_at"]


class RegisterUserSerializer(
    WritableNestedModelSerializer, serializers.ModelSerializer
):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ["firebase_token","email", "phone_number","password", "profile"]

    def validate(self, data):
        """
        Check that at least one of email or phone is present
        """
        if not data["password"]:
            raise serializers.ValidationError(
                "Password is required"
            )
        if not data["phone_number"] or not data["email"]:
            raise serializers.ValidationError(
                "You need to supply user's phone number or email"
            )
        try:
            pan = data["profile"]["pan_number"]
            if len(pan) != 10:
                raise serializers.ValidationError(
                    "Pan number must be of 10 characters."
                )

            try:
                re.findall(PAN_REGEX, pan)[0]
            except IndexError:
                raise serializers.ValidationError("Invalid Pan number format")

        except KeyError:
            raise serializers.ValidationError("Pan number cannot be empty")

        return data

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        UserSetting.objects.create(user=user)
        ZerodhaData.objects.create(local_user=user)
        UserSubscription.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=6)
    phone_number = serializers.CharField(max_length=20, allow_blank=True)
    email = serializers.CharField(max_length=255, allow_blank=True)

    def validate(self, data):

        if not data["phone_number"] or not data["email"]:
            raise serializers.ValidationError(
                "You need to supply user's phone number or email"
            )

        if not data["password"]:
            raise serializers.ValidationError("You need to send the password")

        return data


## Static Data
@extend_schema_serializer(many=False)
class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticData
        fields = ["about_us"]
        read_only_fields = ["about_us"]


@extend_schema_serializer(many=False)
class PrivacyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticData
        fields = ["privacy_policy"]
        read_only_fields = ["privacy_policy"]


@extend_schema_serializer(many=False)
class TermsNConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticData
        fields = ["terms_and_conditions"]
        read_only_fields = ["terms_and_conditions"]


@extend_schema_serializer(many=False)
class ContactDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactData
        fields = ["company_email", "company_number", "company_address"]
        read_only_fields = ["company_email", "company_number", "company_address"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["question", "answer"]
        read_only_fields = ["question", "answer"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "notification_type", "head", "body", "created_at"]
        read_only_fields = ["notification_type", "head", "body", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request:
            validated_data["user"] = request.user
        return super().create(validated_data)


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    firebase_token = serializers.CharField()
    phone_number = serializers.CharField(
        max_length=20, allow_blank=True, required=False
    )
    email = serializers.CharField(max_length=255, allow_blank=True, required=False)
    
    def validate(self, data):
        if not "firebase_token" in  data:
            raise serializers.ValidationError(
                "You need to supply firebase_token"
            )
        if not "phone_number" in data and not "email" in data:
            raise serializers.ValidationError(
                "You need to supply user's phone number or email"
            )
        if "phone_number" in data:
            if not data["phone_number"]:
                raise serializers.ValidationError("Phone number cannot be blank")
        elif "email" in data:
            if not data["email"]:
                raise serializers.ValidationError("Email cannot be blank")

        return data
