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

app_name = "api"

router = DefaultRouter()

router.register(r"profile", UserProfileViewSet, basename="profile")
router.register(r"settings", UserSettingViewSet, basename="settings")
router.register(r"profile-photo", UserProfilePhotoViewSet, basename="profile-photo")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"about-us", AboutUsViewSet, basename="about-us")
router.register(r"privacy-policy", PrivacyPolicyViewSet, basename="privacy-policy")
router.register(
    r"terms-n-conditions", TermsNConditionsViewSet, basename="terms-n-conditions"
)
router.register(r"contact-details", ContactDataViewSet, basename="contact-details")
router.register(r"faqs", FAQViewSet, basename="faqs")


urlpatterns = [
    # Direct urls
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Routers
    path("", include(router.urls)),
]
