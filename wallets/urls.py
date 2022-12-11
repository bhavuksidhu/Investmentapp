from django.urls import path

from adminpanel.views import DashboardView
from wallets.views import AddCoinsView,AddCoinsToAllView

app_name = "wallets"

urlpatterns = [
    path("add-coins/<int:pk>/", AddCoinsView.as_view(), name="add-coins"),
    path("add-coins-to-all/", AddCoinsToAllView.as_view(), name="add-coins-to-all"),
    path("", DashboardView.as_view()),



]
