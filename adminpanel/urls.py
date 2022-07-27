from django.urls import path

from .views import (CustomerDetailView, CustomerEditView, CustomerManagementView, DashboardView,
                    ForgotPasswordView, LoginView, LogoutView, NotificationsView, PasswordResetConfirmationView, PasswordResetView, SettingsView,
                    StaticContentManagementView,InvestingReportView, StockManagementView, StockUploadTemplateView, StockUploadView,SubscriptionManagementView)

app_name = "adminpanel"
urlpatterns = [
    path("", LoginView.as_view(),name="base"),
    path("login/", LoginView.as_view(),name="login"),
    path("logout/", LogoutView.as_view(),name="logout"),
    path("forgot-password/", ForgotPasswordView.as_view(),name="forgot-password"),
    path("password-reset-confirmation/",PasswordResetConfirmationView.as_view(),name="password-reset-confirmation"),
    path("password-reset/",PasswordResetView.as_view(),name="password-reset"),
    path("dashboard/", DashboardView.as_view(),name="dashboard"),
    path("customer-management/", CustomerManagementView.as_view(),name="customer-management"),
    path("customer-detail/<int:pk>/", CustomerDetailView.as_view(),name="customer-detail"),
    path("customer-edit/<int:pk>/",CustomerEditView.as_view(),name="customer-edit"),
    path("investing-reports/",InvestingReportView.as_view(),name="investing-reports"),
    path("subscription-management/",SubscriptionManagementView.as_view(),name="subscription-management"),
    path("stock-upload/",StockUploadView.as_view(),name="stock-upload"),
    path("stock-upload-template/",StockUploadTemplateView.as_view(),name="stock-upload-template"),
    path("stock-management/",StockManagementView.as_view(),name="stock-management"),
    path("static-content-management/", StaticContentManagementView.as_view(),name="static-content-management"),
    path("settings/", SettingsView.as_view(),name="settings"),
    path("notifications/",NotificationsView.as_view(),name="notifications")
]
