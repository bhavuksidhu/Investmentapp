from django.urls import path

from api.zerodha_views import CheckStatus, ExecuteTradeView, KYCView, PostBackView, Redirect, RefreshFundsView

urlpatterns = [
    path("check-status/", CheckStatus.as_view(), name="check-status"),
    path("get-kyc-url/", KYCView.as_view(), name="get-kyc-url"),
    path("redirect/", Redirect.as_view(), name="redirect"),
    path("execute-trade/<uuid:transaction_id>/",ExecuteTradeView.as_view(),name="execute-trade"),
    path("post-back/",PostBackView.as_view(),name="postback"),
    path("refresh-funds/",RefreshFundsView.as_view(),name="refresh-funds")
]
