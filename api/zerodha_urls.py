from django.urls import path

from api.zerodha_views import CheckStatus, KYCView, Redirect

urlpatterns = [
    path("check-status/", CheckStatus.as_view(), name="check-status"),
    path("get-kyc-url/", KYCView.as_view(), name="get-kyc-url"),
    path("redirect/", Redirect.as_view(), name="redirect"),
]
