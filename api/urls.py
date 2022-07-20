from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AboutUsViewSet,
    BasicUserViewSet,
    ContactDataViewSet,
    FAQViewSet,
    LoginView,
    LogoutView,
    MarketFilterViewSet,
    NotificationViewSet,
    PrivacyPolicyViewSet,
    RegisterView,
    ResetPasswordView,
    SubscribeViewSet,
    SubscriptionHistoryViewSet,
    SubscriptionViewSet,
    TermsNConditionsViewSet,
    TransactionViewSet,
    UserProfilePhotoViewSet,
    UserProfileViewSet,
    UserSettingViewSet,
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

#Transactions
router.register(r"transaction",TransactionViewSet,basename="transaction")

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
    # Routers
    path("", include(router.urls)),
    path("zerodha/", include(zerodha_urls)),
]
