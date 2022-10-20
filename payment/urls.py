from django.urls import include, path

from payment.views import CheckOutView, SuccessView, FaliureView

app_name = "payments"

urlpatterns = [
    path("subscribe/",CheckOutView.as_view(),name="subscribe"),
    path("success/", SuccessView.as_view(), name="success"),
    path("faliure/", FaliureView.as_view(), name="faliure"),
]
