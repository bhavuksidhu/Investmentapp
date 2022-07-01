from django.urls import path

from .views import (CustomerDetailView, CustomerManagementView, DashboardView,
                    ForgotPasswordView, LoginView, LogoutView, SettingsView,
                    StaticContentManagementView,InvestingReportView,ComissionManagementView)

app_name = "adminpanel"
urlpatterns = [
    path("", LoginView.as_view(),name="base"),
    path("login/", LoginView.as_view(),name="login"),
    path("logout/", LogoutView.as_view(),name="logout"),
    path("forgot-password/", ForgotPasswordView.as_view(),name="forgot-password"),
    path("dashboard/", DashboardView.as_view(),name="dashboard"),
    path("customer-management/", CustomerManagementView.as_view(),name="customer-management"),
    path("customer-detail/<int:pk>/", CustomerDetailView.as_view(),name="customer-detail"),
    path("investing-reports/",InvestingReportView.as_view(),name="investing-reports"),
    path("comission-management/",ComissionManagementView.as_view(),name="comission-management"),
    path("static-content-management/", StaticContentManagementView.as_view(),name="static-content-management"),
    path("settings/", SettingsView.as_view(),name="settings"),
]
