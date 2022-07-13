from adminpanel.models import FAQ, ContactData, StaticData
from core.models import Notification, UploadedFile, User, UserProfile, UserSetting
from django.utils.datastructures import MultiValueDictKeyError
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    AboutUsSerializer,
    ContactDataSerializer,
    FAQSerializer,
    LoginSerializer,
    NotificationSerializer,
    PrivacyPolicySerializer,
    RegisterUserSerializer,
    ResetPasswordSerializer,
    TermsNConditionsSerializer,
    UploadedFileSerializer,
    UserProfileSerializer,
    UserSettingSerializer,
)
from api.utils import NoDataException, parse_serializer_errors

from .custom_viewsets import GetPostViewSet, GetViewSet, ListGetUpdateViewSet


class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if "email" in request.data:
                try:
                    user = User.objects.get(email=request.data["email"])
                except User.DoesNotExist:
                    user = None
            if "phone_number" in request.data:
                try:
                    user = User.objects.get(phone_number=request.data["phone_number"])
                except User.DoesNotExist:
                    user = None
            if user:
                if not request.data["new_password"]:
                    return Response(
                        {
                            "errors": "Empty password",
                            "status": status.HTTP_400_BAD_REQUEST,
                        }
                    )
                user = request.user
                user.set_password = request.data["new_password"]
                user.save()
            else:
                return Response(
                    {
                        "errors": "No user found",
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )
            return Response(
                {
                    "errors": None,
                    "status": status.HTTP_200_OK,
                }
            )
        else:
            return Response(
                {
                    "errors": serializer.errors,
                    "status": status.HTTP_400_BAD_REQUEST,
                }
            )


class RegisterView(APIView):
    serializer_class = RegisterUserSerializer

    @extend_schema(
        request=inline_serializer(
            name="register_request",
            fields={
                "firebase_token": serializers.CharField(),
                "phone_number": serializers.CharField(max_length=20),
                "email": serializers.EmailField(allow_blank=True),
                "password": serializers.CharField(max_length=20),
                "profile": UserProfileSerializer(),
            },
        ),
        responses=inline_serializer(
            name="register_response",
            fields={
                "errors": serializers.CharField(),
                "token": serializers.CharField(allow_null=True),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request: Request, *args, **kwargs):
        try:
            firebase_token = request.data["firebase_token"]
        except:
            return Response(
                {
                    "errors": "Firebase token not present",
                    "token": None,
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = str(Token.objects.get_or_create(user=user)[0])
            return Response(
                {
                    "errors": None,
                    "token": token,
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "errors": serializer.errors,
                    "token": None,
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(APIView):
    @extend_schema(
        request=LoginSerializer,
        responses=inline_serializer(
            name="login_response",
            fields={
                "errors": serializers.CharField(),
                "token": serializers.CharField(allow_null=True),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request: Request, *args, **kwargs):
        if "password" in request.data:
            if "phone_number" in request.data and request.data["phone_number"]:
                phone_number = request.data["phone_number"]
                try:
                    user: User = User.objects.get(phone_number=phone_number)
                except User.DoesNotExist:
                    return Response(
                        {
                            "errors": "No user with that phone number.",
                            "token": None,
                            "status": status.HTTP_404_NOT_FOUND,
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            elif "email" in request.data and request.data["email"]:
                email = request.data["email"]
                try:
                    user: User = User.objects.get(email=email)
                except User.DoesNotExist:
                    return Response(
                        {
                            "errors": "No user with that email.",
                            "token": None,
                            "status": status.HTTP_404_NOT_FOUND,
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )
            else:
                return Response(
                    {
                        "errors": "You need to supply user's phone number or email to login.",
                        "token": None,
                        "status": status.HTTP_400_BAD_REQUEST,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.check_password(request.data["password"]):

                token = str(Token.objects.get_or_create(user=user)[0])
                return Response(
                    {
                        "errors": None,
                        "token": token,
                        "status": status.HTTP_200_OK,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "errors": "Invalid Password",
                        "token": None,
                        "status": status.HTTP_400_BAD_REQUEST,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {
                    "errors": "No Password present in body",
                    "token": None,
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="logout",
            fields={
                "errors": serializers.CharField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request: Request, *args, **kwargs):
        request.user.auth_token.delete()
        return Response(
            {
                "errors": None,
                "status": status.HTTP_200_OK,
            }
        )


@extend_schema(
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {"file": {"type": "string", "format": "binary"}},
        }
    },
)
class UserProfilePhotoViewSet(GetPostViewSet):
    serializer_class = UploadedFileSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return UploadedFile.objects.get(profile=self.request.user.profile)
        except (UserProfile.DoesNotExist, UploadedFile.DoesNotExist):
            raise NoDataException


class UserProfileViewSet(GetPostViewSet):
    serializer_class = UserProfileSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            raise NoDataException


class UserSettingViewSet(GetPostViewSet):
    serializer_class = UserSettingSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return UserSetting.objects.get(user=self.request.user)
        except UserSetting.DoesNotExist:
            raise NoDataException


class AboutUsViewSet(GetViewSet):
    serializer_class = AboutUsSerializer

    def get_queryset(self):
        return StaticData.objects.last()


class PrivacyPolicyViewSet(GetViewSet):
    serializer_class = PrivacyPolicySerializer

    def get_queryset(self):
        return StaticData.objects.last()


class TermsNConditionsViewSet(GetViewSet):
    serializer_class = TermsNConditionsSerializer

    def get_queryset(self):
        return StaticData.objects.last()


class ContactDataViewSet(GetViewSet):
    serializer_class = ContactDataSerializer

    def get_queryset(self):
        return ContactData.objects.last()


class FAQViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FAQSerializer

    def get_queryset(self):
        return FAQ.objects.all()


class NotificationViewSet(ListGetUpdateViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
