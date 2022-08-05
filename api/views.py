import datetime
from datetime import timedelta

from adminpanel.models import FAQ, AdminNotification, ContactData, StaticData
from core.models import (
    EmailVerificationRecord,
    MarketQuote,
    Notification,
    Transaction,
    UploadedFile,
    User,
    UserProfile,
    UserSetting,
    UserSubscription,
    ZerodhaData,
)
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotFound
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    AboutUsSerializer,
    BasicUserSerializer,
    ContactDataSerializer,
    FAQSerializer,
    FundsSerializer,
    InsightSerializer,
    JournalGroupedByDateSerializer,
    JournalSerializer,
    LoginSerializer,
    MarketQuoteSerializer,
    NotificationSerializer,
    PortfolioSerializer,
    PrivacyPolicySerializer,
    RegisterUserSerializer,
    ResetPasswordSerializer,
    TermsNConditionsSerializer,
    TradeSerializer,
    TransactionGroupedByDateSerializer,
    TransactionSerializer,
    UploadedFileSerializer,
    UserProfileSerializer,
    UserSettingSerializer,
    UserSubscriptionHistorySerializer,
    UserSubscriptionSerializer,
)
from api.utils import NoDataException, StandardResultsSetPagination

from .custom_viewsets import GetPostViewSet, GetViewSet, ListGetUpdateViewSet


class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if "email" in request.data:
                try:
                    user: User = User.objects.get(email=request.data["email"])
                except User.DoesNotExist:
                    user = None
            if "phone_number" in request.data:
                try:
                    user: User = User.objects.get(
                        phone_number=request.data["phone_number"]
                    )
                except User.DoesNotExist:
                    user = None
            firebase_token = request.data.get("firebase_token")

            if firebase_token != user.firebase_token:
                return Response(
                    {
                        "errors": "Invalid firebase token!",
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )

            if user:
                if not request.data["new_password"]:
                    return Response(
                        {
                            "errors": "Empty password",
                            "status": status.HTTP_400_BAD_REQUEST,
                        }
                    )
                user = request.user
                user.set_password(request.data["new_password"])
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
            AdminNotification.objects.create(
                title=f"New user signed-up!",
                content=f"A new user has signed up, ID : CU{user.id}.",
            )
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


class BasicUserViewSet(GetPostViewSet):
    serializer_class = BasicUserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user


class UserSettingViewSet(GetPostViewSet):
    serializer_class = UserSettingSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return UserSetting.objects.get(user=self.request.user)
        except UserSetting.DoesNotExist:
            raise NoDataException


class GetFundsViewSet(GetViewSet):
    serializer_class = FundsSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        try:
            return ZerodhaData.objects.get(local_user=self.request.user)
        except ZerodhaData.DoesNotExist:
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


class SubscribeViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSubscriptionHistorySerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)

        subscription: UserSubscription = self.request.user.subscription
        if subscription.date_to and subscription.date_from:
            subscription.date_to = subscription.date_to + timedelta(days=365)
        else:
            subscription.date_from = timezone.now().date()
            subscription.date_to = timezone.now().date() + timedelta(days=365)

        subscription.active = True
        subscription.save()

        AdminNotification.objects.create(
            title=f"Subscription Purchased!",
            content=f"User - CU{request.user.id}, has just purchased a subscription!",
        )

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class SubscriptionViewSet(GetViewSet):
    serializer_class = UserSubscriptionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.subscription


class SubscriptionHistoryViewSet(GetViewSet):
    serializer_class = UserSubscriptionHistorySerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    many = True

    def get_queryset(self):
        return self.request.user.subscription.history.all()


class MarketFilterViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pagination_class = StandardResultsSetPagination
    serializer_class = MarketQuoteSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        price = self.request.GET.get("price", None)
        keyword = self.request.GET.get("keyword", None)

        price = float(price)
        lower_price = price - 1000

        query = MarketQuote.objects.filter(price__lte=price, price__gte=lower_price)

        if keyword:
            query = query.filter(
                Q(company_name__icontains=keyword)
                | Q(trading_symbol__icontains=keyword)
            )

        return query

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="price",
                location=OpenApiParameter.QUERY,
                description="Last Price",
                required=True,
                type=float,
            ),
            OpenApiParameter(
                name="keyword",
                location=OpenApiParameter.QUERY,
                description="Keyword",
                required=False,
                type=str,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[OpenApiParameter("id", int, OpenApiParameter.PATH)]
    )
)
class TransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    pagination_class = StandardResultsSetPagination
    serializer_class = TransactionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.transactions.filter()

    @extend_schema(responses=TransactionGroupedByDateSerializer)
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        transactions = self.paginate_queryset(queryset)

        grouped_by_date = {}
        for transaction in transactions:
            created_at = str(transaction.created_at.date())
            if created_at in grouped_by_date:
                grouped_by_date[created_at].append(transaction.__dict__)
            else:
                grouped_by_date[created_at] = [transaction.__dict__]
        grouped_by_date = [
            {"date": key, "transactions": value}
            for key, value in grouped_by_date.items()
        ]

        print(grouped_by_date)

        serializer = TransactionGroupedByDateSerializer(data=grouped_by_date, many=True)
        if serializer.is_valid():
            return self.get_paginated_response(serializer.data)
        else:
            return Response(
                {
                    "errors": serializer.errors,
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status.HTTP_400_BAD_REQUEST
            )


class TransactionLatestView(APIView):
    serializer_class = TransactionSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        transaction = self.request.user.transactions.first()
        serializer = self.serializer_class(transaction)
        return Response(serializer.data)


class PortFolioView(APIView):
    serializer_class = PortfolioSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        transactions = request.user.transactions.filter(verified=True)

        transaction_data = {}
        for transaction in transactions:
            symbol = transaction.trading_symbol
            if symbol in transaction_data:
                if transaction.transaction_type == "SELL":
                    transaction_data[symbol]["quantity"] -= transaction.quantity
                    transaction_data[symbol]["purchased_value"] -= transaction.amount
                else:
                    transaction_data[symbol]["quantity"] += transaction.quantity
                    transaction_data[symbol]["purchased_value"] += transaction.amount
            else:
                transaction_data[symbol] = {
                    "trading_symbol": symbol,
                    "exchange": transaction.exchange,
                    "quantity": 0,
                    "purchased_value": 0.0,
                }

                if transaction.transaction_type == "SELL":
                    transaction_data[symbol]["quantity"] = -transaction.quantity
                    transaction_data[symbol]["purchased_value"] = -transaction.amount
                else:
                    transaction_data[symbol]["quantity"] = transaction.quantity
                    transaction_data[symbol]["purchased_value"] += transaction.amount

        portfolio_list = [v for k, v in transaction_data.items() if v["quantity"] != 0]
        stocks_list = [k for k, v in transaction_data.items() if v["quantity"] != 0]
        current_stocks_data = {
            x["trading_symbol"]: x
            for x in MarketQuote.objects.filter(trading_symbol__in=stocks_list).values(
                "company_name", "price", "trading_symbol"
            )
        }

        for entry in portfolio_list:
            current_data = current_stocks_data[entry["trading_symbol"]]
            entry["company_name"] = current_data["company_name"]
            entry["current_value"] = current_data["price"] * entry["quantity"]

        num_of_transactions = len(transactions)
        total_purchase_value = sum([x["purchased_value"] for x in portfolio_list])
        total_current_value = sum(x["current_value"] for x in portfolio_list)

        data = {
            "num_of_transactions": num_of_transactions,
            "total_purchase_value": total_purchase_value,
            "total_current_value": total_current_value,
            "portfolio_list": portfolio_list,
        }

        s = PortfolioSerializer(data=data)
        print(s.is_valid())
        return Response(s.data)


class JournalViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pagination_class = StandardResultsSetPagination
    serializer_class = JournalGroupedByDateSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)
        query = self.request.user.transactions.filter()
        if from_date:
            query = query.filter(created_at__date__gte=from_date)
        if to_date:
            query = query.filter(created_at__date__lte=to_date)
        return query

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="from_date",
                location=OpenApiParameter.QUERY,
                description="From date",
                required=False,
                type=datetime.date,
            ),
            OpenApiParameter(
                name="to_date",
                location=OpenApiParameter.QUERY,
                description="To Date",
                required=False,
                type=datetime.date,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        entries = self.paginate_queryset(queryset)
        grouped_by_date = {}
        for entry in entries:
            created_at = str(entry.created_at.date())
            if created_at in grouped_by_date:
                grouped_by_date[created_at].append(entry.__dict__)
            else:
                grouped_by_date[created_at] = [entry.__dict__]
        grouped_by_date = [
            {"date": key, "entries": value}
            for key, value in grouped_by_date.items()
        ]
        serializer = JournalGroupedByDateSerializer(data=grouped_by_date, many=True)
        if serializer.is_valid():
            return self.get_paginated_response(serializer.data)
        else:
            return Response(
                {
                    "errors": serializer.errors,
                    "status": status.HTTP_400_BAD_REQUEST,
                }
            )


class InvestmentInsightViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = InsightSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)
        query = self.request.user.insights.all()
        if from_date:
            query = query.filter(created_at__date__gte=from_date)
        if to_date:
            query = query.filter(created_at__date__lte=to_date)
        return query

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="from_date",
                location=OpenApiParameter.QUERY,
                description="From date",
                required=False,
                type=datetime.date,
            ),
            OpenApiParameter(
                name="to_date",
                location=OpenApiParameter.QUERY,
                description="To Date",
                required=False,
                type=datetime.date,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TradeViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.transactions.all()

    @extend_schema(
        responses=inline_serializer(
            name="trade_response",
            fields={
                "trade_url": serializers.CharField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def create(self, request, *args, **kwargs):
        try:
            transaction_obj: Transaction = Transaction.objects.create(
                **{"user": request.user, **request.data}
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    "trade_url": None,
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        trade_url = request.build_absolute_uri("/")[:-1] + reverse(
            "api:execute-trade", kwargs={"transaction_id": transaction_obj.uid}
        )
        return Response(
            {
                "trade_url": trade_url,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class CheckEmailPassword(APIView):
    @extend_schema(
        request=inline_serializer(
            name="check_email_pass_request",
            fields={
                "email": serializers.CharField(allow_null=True),
                "phone_number": serializers.CharField(allow_null=True),
            },
        ),
        responses=inline_serializer(
            name="check_email_pass_response",
            fields={
                "user_exists": serializers.BooleanField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request: Request, *args, **kwargs):
        exists = False
        if "email" in request.data:
            try:
                User.objects.get(email=request.data["email"])
                exists = True
            except User.DoesNotExist:
                pass

        if "phone_number" in request.data:
            try:
                User.objects.get(phone_number=request.data["phone_number"])
                exists = True
            except User.DoesNotExist:
                pass

        return Response(
            {
                "user_exists": exists,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(View):
    def get(self, request, *args, **kwargs):
        uid = request.GET.get("uid", None)
        if uid:
            try:
                record = EmailVerificationRecord.objects.get(uid=uid)
                user = record.user
                user.is_email_verified = True
                user.save()
                record.delete()
                return HttpResponse("Email Verification Complete!")
            except EmailVerificationRecord.DoesNotExist:
                return HttpResponseNotFound("Invalid URL")
        else:
            return HttpResponseNotFound("Invalid URL")


class SendVerififcationEmailView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses=inline_serializer(
            name="verify_email_response",
            fields={
                "errors": serializers.CharField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def get(self, request, *args, **kwargs):
        if request.user.is_email_verified:
            return Response(
                {
                    "errors": "Email already verified.",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            email_verification: EmailVerificationRecord = (
                EmailVerificationRecord.objects.create(user=request.user)
            )
            verification_url = (
                request.build_absolute_uri("/")[:-1]
                + reverse("api:email-verification")
                + f"?uid={str(email_verification.uid)}"
            )

            send_mail(
                "Email verification",
                f"Please click the link to verification your Email {verification_url}",
                "investthrift@gmail.com",
                [request.user.email],
                fail_silently=False,
            )

            return Response(
                {
                    "errors": None,
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            email_verification.delete()
            return Response(
                {
                    "errors": f"{e}",
                    "status": status.HTTP_400_BAD_REQUEST,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
