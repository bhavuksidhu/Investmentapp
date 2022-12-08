from django.urls import path

from adminpanel.views import DashboardView
from wallets.views import AddCoinsView

app_name = "wallets"

urlpatterns = [
    path("add-coins/<int:pk>/", AddCoinsView.as_view(), name="add-coins"),
    path("", DashboardView.as_view()),
]
