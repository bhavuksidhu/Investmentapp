from mimetypes import guess_type

from adminpanel.models import FAQ, ContactData, StaticData
from attr import field
from drf_spectacular.utils import extend_schema_serializer
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from core.models import (
    Notification,
    UploadedFile,
    User,
    UserProfile,
    UserSetting,
)

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


@extend_schema_serializer(many=False)
class UserProfileSerializer(serializers.ModelSerializer):
    profile_photo = UploadedFileSerializer(allow_null=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "gender",
            "age",
            "profile_photo",
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
        fields = [
            "notification_preference",
            "device_token",
            "device_type"
        ]

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request:
            validated_data["user"] = request.user
        return super().create(validated_data)


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


class RegisterUserSerializer(WritableNestedModelSerializer, serializers.ModelSerializer):
    profile = UserProfileSerializer()

    class Meta:
        model = User
        fields = ["email", "phone_number","profile"]

    def validate(self, data):
        """
        Check that at least one of email or phone is present
        """
        if not data["phone_number"] or not data["email"]:
            raise serializers.ValidationError("You need to supply user's phone number")
        return data
    
    def create(self, validated_data):
        user = super().create(validated_data)
        UserSetting.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6)
    phone_number = serializers.CharField(max_length=20)

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
        fields = ["company_number", "company_address"]
        read_only_fields = ["company_number", "company_address"]


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ["question", "answer"]
        read_only_fields = ["question", "answer"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "head", "body", "created_at"]
        read_only_fields = ["head", "body", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request:
            validated_data["user"] = request.user
        return super().create(validated_data)


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
