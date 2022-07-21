from django.urls import path

from .views import (CustomerAddView, CustomerDetailView, CustomerEditView, CustomerManagementView, DashboardView,
                    ForgotPasswordView, LoginView, LogoutView, SettingsView,
                    StaticContentManagementView,InvestingReportView, StockManagementView, StockUploadTemplateView, StockUploadView,SubscriptionManagementView)

app_name = "adminpanel"
urlpatterns = [
    path("", LoginView.as_view(),name="base"),
    path("login/", LoginView.as_view(),name="login"),
    path("logout/", LogoutView.as_view(),name="logout"),
    path("forgot-password/", ForgotPasswordView.as_view(),name="forgot-password"),
    path("dashboard/", DashboardView.as_view(),name="dashboard"),
    path("customer-management/", CustomerManagementView.as_view(),name="customer-management"),
    path("customer-add/",CustomerAddView.as_view(),name="customer-add"),
    path("customer-detail/<int:pk>/", CustomerDetailView.as_view(),name="customer-detail"),
    path("customer-edit/<int:pk>/",CustomerEditView.as_view(),name="customer-edit"),
    path("investing-reports/",InvestingReportView.as_view(),name="investing-reports"),
    path("subscription-management/",SubscriptionManagementView.as_view(),name="subscription-management"),
    path("stock-upload/",StockUploadView.as_view(),name="stock-upload"),
    path("stock-upload-template/",StockUploadTemplateView.as_view(),name="stock-upload-template"),
    path("stock-management/",StockManagementView.as_view(),name="stock-management"),
    path("static-content-management/", StaticContentManagementView.as_view(),name="static-content-management"),
    path("settings/", SettingsView.as_view(),name="settings"),
]
