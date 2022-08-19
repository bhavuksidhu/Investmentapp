from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AboutUsViewSet,
    BasicUserViewSet,
    CheckOldPassword,
    ContactDataViewSet,
    FAQViewSet,
    GetFundsViewSet,
    InvestmentInsightViewSet,
    JournalViewSet,
    LoginView,
    LogoutView,
    MarketFilterViewSet,
    NotificationViewSet,
    PortFolioView,
    PrivacyPolicyViewSet,
    RegisterView,
    ResetPasswordView,
    SendVerififcationEmailView,
    SubscribeViewSet,
    SubscriptionHistoryViewSet,
    SubscriptionViewSet,
    TermsNConditionsViewSet,
    TradeViewSet,
    TransactionLatestView,
    TransactionViewSet,
    UserProfilePhotoViewSet,
    UserProfileViewSet,
    UserSettingViewSet,
    CheckEmailPhoneNumber,
    InvestmentInsightViewSet,
    VerifyEmailView
)
from api.zerodha_urls import urlpatterns as zerodha_urls

app_name = "api"

router = DefaultRouter()

router.register(r"profile", UserProfileViewSet, basename="profile")
router.register(r"profile/user-data",BasicUserViewSet,basename="user-data")
router.register(
    r"profile/profile-photo", UserProfilePhotoViewSet, basename="profile-photo"
)
router.register(r"settings", UserSettingViewSet, basename="settings")
router.register(r"notifications", NotificationViewSet, basename="notifications")

router.register(r"market/filter",MarketFilterViewSet,basename="market-filter")

router.register(r"funds",GetFundsViewSet,basename="get-funds")

#Transactions
router.register(r"investment-insight/insights",InvestmentInsightViewSet,basename="investment-insight")
router.register(r"investment-insight/transactions",TransactionViewSet,basename="transaction")
router.register(r"trade",TradeViewSet,basename="trade")
router.register(r"journal",JournalViewSet,basename="journal")

#Subscriptions
router.register(r"subscription/subscribe",SubscribeViewSet,basename="subscribe")
router.register(r"subscription/detail",SubscriptionViewSet,basename="subscription-detail")
router.register(r"subscription/history",SubscriptionHistoryViewSet,basename="subscription-history")

#Static
router.register(r"static/about-us", AboutUsViewSet, basename="about-us")
router.register(
    r"static/privacy-policy", PrivacyPolicyViewSet, basename="privacy-policy"
)
router.register(
    r"static/terms-n-conditions", TermsNConditionsViewSet, basename="terms-n-conditions"
)
router.register(
    r"static/contact-details", ContactDataViewSet, basename="contact-details"
)
router.register(r"static/faqs", FAQViewSet, basename="faqs")


urlpatterns = [
    # Direct urls
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("check/email-phone/",CheckEmailPhoneNumber.as_view(),name="check-email-phone"),
    path("check/old-password/",CheckOldPassword.as_view(),name="check-old-password"),
    path("portfolio/",PortFolioView.as_view(),name="portfolio"),
    path("investment-insight/transactions/latest/",TransactionLatestView.as_view(),name="transaction-latest"),
    path("verify/send-verification-email/",SendVerififcationEmailView.as_view(),name="send-verification-email"),
    path("verify/email/",VerifyEmailView.as_view(),name="email-verification"),
    # Routers
    path("", include(router.urls)),
    path("zerodha/", include(zerodha_urls)),
]
