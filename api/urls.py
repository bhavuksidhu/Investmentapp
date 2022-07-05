from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AboutUsViewSet,
    ContactDataViewSet,
    FAQViewSet,
    LoginView,
    LogoutView,
    NotificationViewSet,
    PrivacyPolicyViewSet,
    RegisterView,
    SendOTPView,
    TermsNConditionsViewSet,
    UserProfilePhotoViewSet,
    UserProfileViewSet,
    UserSettingViewSet,
)
from api.zerodha_views import ZerodhaCheckStatus, ZerodhaKYCView, ZerodhaRedirect

app_name = "api"

router = DefaultRouter()

router.register(r"profile", UserProfileViewSet, basename="profile")
router.register(r"settings", UserSettingViewSet, basename="settings")
router.register(r"profile/profile-photo", UserProfilePhotoViewSet, basename="profile-photo")
router.register(r"notifications", NotificationViewSet, basename="notifications")
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
    path("auth/send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    # Routers
    path("", include(router.urls)),
    path(
        "zerodha/check-status",
        ZerodhaCheckStatus.as_view(),
        name="zerodha-check-status",
    ),
    path("zerodha/get-kyc-url", ZerodhaKYCView.as_view(), name="zerodha-get-kyc-url"),
    path("zerodha/redirect", ZerodhaRedirect.as_view(), name="zerodha-redirect"),
]
