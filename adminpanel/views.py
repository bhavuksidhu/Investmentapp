from datetime import datetime, timedelta

from core.models import User
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView


# Create your views here.
class LoginView(View):
    template = "login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            return redirect("adminpanel:dashboard")
        return render(request, self.template)

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", None)
        password = request.POST.get("password", None)

        if email and password:
            try:
                user: User = User.objects.get(email=email)
                if user.is_superuser:
                    if user.check_password(password):
                        login(request, user)
                        return redirect("adminpanel:dashboard")
                    else:
                        messages.add_message(
                            request, messages.ERROR, "Invalid password."
                        )
                else:
                    messages.add_message(
                        request,
                        messages.INFO,
                        "You do not have permissions to access adminpanel.",
                    )
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, "No Such User")
        else:
            messages.add_message(
                request, messages.ERROR, "Email & Password must be supplied to login."
            )
        return render(request, self.template)


class LogoutView(View):
    template = "login.html"

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("adminpanel:login")


class ForgotPasswordView(View):
    template = "forgot_password.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)


class DashboardView(View):
    template = "dashboard.html"

    def get(self, request, *args, **kwargs):

        context = {}

        user_query = User.objects.filter(
            is_superuser=False, is_staff=False, is_active=True
        )

        from_date = request.GET.get("from_date", None)
        to_date = request.GET.get("to_date", None)

        from_period = request.GET.get("from_period", None)

        if from_date and to_date:
            user_query = user_query.filter(created_at__date__range=[from_date, to_date])
            
        elif from_period:
            today = datetime.today()
            if from_period == "Today":
                filter_date = today.date()
            elif from_period == "This Week":
                filter_date = today - timedelta(days=7)
                filter_date = filter_date.date()
            else:
                filter_date = today - timedelta(days=30)
                filter_date = filter_date.date()

            user_query = user_query.filter(created_at__date__gte=filter_date)

        total_active_users = user_query.count()

        total_revenue = 0

        context["total_active_users"] = total_active_users
        context["total_revenue"] = total_revenue
        context["from_period"] = from_period
        context["from_date"] = from_date
        context["to_date"] = to_date

        return render(
            request,
            self.template,
            context=context,
        )


class CustomerManagementView(ListView):
    template_name = "customer_management.html"
    model = User
    context_object_name = "user_list"

    def get_queryset(self):
        q = self.request.GET.get("q", None)
        if q:
            return (
                User.objects.select_related()
                .filter(is_superuser=False)
                .filter(Q(email__icontains=q) | Q(phone_number__icontains=q))
            )
        else:
            return User.objects.select_related().filter(is_superuser=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", None)
        return context


class CustomerDetailView(DetailView):
    template_name = "customer_details.html"
    mode = User
    context_object_name = "user"

    def get_queryset(self):
        return (
            User.objects.select_related().filter(id=self.kwargs.get("pk"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)

        context["from_date"] = from_date
        context["to_date"] = to_date

        return context

class InvestingReportView(View):
    template = "investing_reports.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)

class ComissionManagementView(View):
    template = "comission_management.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)

class StaticContentManagementView(View):
    template = "static_content_management.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)


class SettingsView(View):
    template = "settings.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)

    def post(self, request, *args, **kwargs):
        old_password = request.POST.get("old_password", None)
        new_password = request.POST.get("new_password", None)
        new_password_2 = request.POST.get("new_password_2", None)

        if old_password and new_password and new_password_2:
            if new_password != new_password_2:
                messages.add_message(
                    request, messages.ERROR, "New Passwords do not match."
                )
            else:
                if request.user.check_password(old_password):
                    request.user.set_password(new_password)
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                    messages.add_message(request, messages.SUCCESS, "Password updated!")
                else:
                    messages.add_message(request, messages.ERROR, "Wrong old password.")
        else:
            messages.add_message(
                request, messages.ERROR, "Password & New Password must be supplied."
            )

        return render(request, self.template)
