import json
from datetime import datetime, timedelta

import pandas as pd
from core.models import (
    Stock,
    User,
    UserProfile,
    UserSubscription,
    UserSubscriptionHistory,
)
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.http import FileResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from adminpanel.models import (
    FAQ,
    AdminNotification,
    ContactData,
    PasswordReset,
    StaticData,
)


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

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", None)
        user = User.objects.filter(email=email, is_superuser=True).first()
        if user:
            password_reset: PasswordReset = PasswordReset.objects.create(user=user)
            reset_url = (
                request.build_absolute_uri("/")[:-1]
                + reverse("adminpanel:password-reset")
                + f"?uid={str(password_reset.uid)}"
            )
            send_mail(
                "Password Reset",
                f"Please click the link to reset your password {reset_url}",
                "investthrift@gmail.com",
                [email],
                fail_silently=False,
            )
        return redirect("adminpanel:password-reset-confirmation")


class PasswordResetConfirmationView(View):
    template = "password-reset-confirmation.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)


class PasswordResetView(View):
    template = "password-reset.html"

    def get(self, request, *args, **kwargs):
        uid = request.GET.get("uid", None)
        if uid:
            try:
                PasswordReset.objects.get(uid=uid)
                return render(request, self.template, {"uid": uid})
            except PasswordReset.DoesNotExist:
                return HttpResponseNotFound("Invalid URL")
        else:
            return HttpResponseNotFound("Invalid URL")

    def post(self, request, *args, **kwargs):
        uid = request.GET.get("uid", None)
        password = request.POST.get("password", None)
        password2 = request.POST.get("password2", None)

        try:
            password_reset_obj: PasswordReset = PasswordReset.objects.get(uid=uid)
        except PasswordReset.DoesNotExist:
            return HttpResponseNotFound("Invalid URL")

        user = password_reset_obj.user

        if password == password2:
            user.set_password(password)
            user.save()
            messages.add_message(request, messages.SUCCESS, "Password reset complete!")
            password_reset_obj.delete()
        else:
            messages.add_message(
                request,
                messages.ERROR,
                "Password reset failed, Passwords do not match.",
            )

        return redirect("adminpanel:login")


class DashboardView(View):
    template = "dashboard.html"

    def get(self, request, *args, **kwargs):

        context = {}
        header = "Today"

        user_query = User.objects.filter(
            is_superuser=False, is_staff=False, is_active=True
        )
        subscriber_query = UserSubscriptionHistory.objects.filter()

        from_date = request.GET.get("from_date", None)
        to_date = request.GET.get("to_date", None)

        from_period = request.GET.get("from_period", None)
        
        if from_date or to_date:
            if from_date:
                user_query = user_query.filter(created_at__date__gte=from_date)
                subscriber_query = subscriber_query.filter(
                    created_at__date__gte=from_date
                )
            if to_date:
                user_query = user_query.filter(created_at__date__lte=to_date)
                subscriber_query = subscriber_query.filter(
                    created_at__date__lte=to_date
                )
            header = f"From {from_date} to {to_date}"

        elif from_period:
            today = datetime.today()
            if from_period == "Today":
                header = "Today"
                filter_date = today.date()
            elif from_period == "This Week":
                header = "This Week"
                filter_date = today - timedelta(days=7)
                filter_date = filter_date.date()
            else:
                header = "This month"
                filter_date = today - timedelta(days=30)
                filter_date = filter_date.date()

            user_query = user_query.filter(created_at__date__gte=filter_date)
            subscriber_query = subscriber_query.filter(
                created_at__date__gte=filter_date
            )

        context["total_active_users"] = user_query.count()
        context["total_revenue"] = subscriber_query.aggregate(Sum("amount"))[
            "amount__sum"
        ]
        if context["total_revenue"] is None:
            context["total_revenue"] = 0
        context["total_subscribed_users"] = subscriber_query.count()
        context["from_period"] = from_period
        context["from_date"] = from_date
        context["to_date"] = to_date
        context["today_date"] = datetime.today().strftime('%Y-%m-%d')
        context["header"] = header

        return render(
            request,
            self.template,
            context=context,
        )


class CustomerManagementView(ListView):
    template_name = "customer_management.html"
    model = User
    context_object_name = "user_list"
    paginate_by = 5

    def get_queryset(self):
        q = self.request.GET.get("q", None)
        if q:
            q = q.strip()
            if "CU" in q:
                try:
                    user_id = int(q.replace("CU",""))
                except:
                    user_id = None
            else:
                user_id = None

            if user_id:
                return (
                    User.objects.select_related("profile")
                    .filter(is_superuser=False)
                    .filter(id=user_id)
                )
            else:
                return (
                    User.objects.select_related("profile")
                    .filter(is_superuser=False)
                    .filter(
                        Q(email__icontains=q)
                        | Q(phone_number__icontains=q)
                        | Q(profile__first_name__icontains=q)
                    )
                )
        else:
            return User.objects.select_related().filter(is_superuser=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", None)
        return context

    def post(self, request, *args, **kwargs):
        todo = request.POST.get("todo", None)
        user_id = request.POST.get("user_id", None)

        if todo and user_id:
            try:
                user: User = User.objects.get(id=int(user_id))

                if todo == "block":
                    user.is_active = False
                    user.save()
                elif todo == "unblock":
                    user.is_active = True
                    user.save()
                elif todo == "delete":
                    user.delete()

            except User.DoesNotExist:
                return JsonResponse({"message": "Failed to find user"})

        return JsonResponse({"message": "OK"})


class CustomerDetailView(DetailView):
    template_name = "customer_detail.html"
    mode = User
    context_object_name = "user"

    def get_queryset(self):
        return User.objects.select_related("profile").filter(id=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)

        context["from_date"] = from_date
        context["to_date"] = to_date

        return context


class CustomerEditView(DetailView):
    template_name = "customer_edit.html"
    mode = User
    context_object_name = "user"

    def get_queryset(self):
        return User.objects.select_related("profile").filter(id=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)

        context["from_date"] = from_date
        context["to_date"] = to_date

        return context

    def post(self, request, *args, **kwargs):
        first_name = request.POST.get("first_name", None)
        last_name = request.POST.get("last_name", None)
        email = request.POST.get("email", None)
        phone_number = request.POST.get("phone_number", None)
        pan_number = request.POST.get("pan_number", None)
        date_of_birth = request.POST.get("date_of_birth", None)
        gender = request.POST.get("gender", None)
        address = request.POST.get("address", None)

        try:
            user: User = User.objects.get(id=self.kwargs.get("pk"))
            profile: UserProfile = user.profile
        except User.DoesNotExist:
            return self.get(self, request, *args, **kwargs)

        print(first_name)

        if first_name:
            profile.first_name = first_name
        if last_name:
            profile.last_name = last_name
        if email:
            user.email = email
        if phone_number:
            user.phone_number = phone_number
        if pan_number:
            profile.pan_number = pan_number
        if date_of_birth:
            profile.date_of_birth = date_of_birth
        if gender:
            profile.gender = gender
        if address:
            profile.address = address

        try:
            profile.save()
            user.save()
        except Exception as e:
            print(e)

        return redirect("adminpanel:customer-edit", self.kwargs.get("pk"))


class InvestingReportView(View):
    template = "investing_reports.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template)


class SubscriptionManagementView(ListView):
    template_name = "subscription_management.html"
    model = UserSubscription
    context_object_name = "subscriptions"
    paginate_by = 5

    def get_queryset(self):
        q = self.request.GET.get("q", None)

        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)

        query = UserSubscription.objects.select_related()

        if from_date:
            query = query.filter(date_from__gte=from_date)
        elif to_date:
            query = query.filter(date_to__lte=to_date)

        if q:
            query = query.filter(
                Q(user__email__icontains=q)
                | Q(user__phone_number__icontains=q)
                | Q(user__profile__first_name__icontains=q)
            )

        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["from_date"] = self.request.GET.get("from_date", None)
        context["to_date"] = self.request.GET.get("to_date", None)
        context["today_date"] = datetime.today().strftime('%Y-%m-%d')
        return context


class StockManagementView(ListView):
    template_name = "stock_management.html"
    model = Stock
    context_object_name = "stocks"
    paginate_by = 5

    def get_queryset(self):
        q = self.request.GET.get("q", None)
        query = Stock.objects.all()
        if q:
            query = query.filter(Q(symbol__icontains=q))
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class StockUploadView(View):
    template_name = "stock_upload.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        df = pd.read_excel(request.FILES.get("stock_file"))
        print(df)
        print(df["exchange"].isnull().values.any())
        if df["exchange"].isnull().values.any() or df["symbol"].isnull().values.any():
            messages.add_message(
                request, messages.ERROR, "Exchance & Symbol columns can't be empty!"
            )
            return redirect("adminpanel:stock-upload")

        Stock.objects.all().delete()
        [Stock.objects.create(**x) for x in df.T.to_dict().values()]
        return redirect("adminpanel:stock-management")


class StockUploadTemplateView(View):
    def get(self, request, *args, **kwagrs):
        return FileResponse(open("stocks_template.xlsx", "rb"))


class StaticContentManagementView(View):
    template = "static_content_management.html"

    def get(self, request, *args, **kwargs):
        static_content = StaticData.objects.select_related("contact_data").first()
        faqs = FAQ.objects.all()
        context = {"static_content": static_content, "faqs": faqs}
        return render(request, self.template, context=context)

    def post(self, request, *args, **kwargs):
        contact_data = request.POST.get("contact_data", None)
        about_us = request.POST.get("about_us", None)
        terms_and_conditions = request.POST.get("terms_and_conditions", None)
        privacy_policy = request.POST.get("privacy_policy", None)
        faqs = request.POST.get("faqs", None)

        static_content_obj: StaticData = StaticData.objects.select_related(
            "contact_data"
        ).first()
        contact_data_obj: ContactData = static_content_obj.contact_data

        if contact_data:
            contact_data = json.loads(contact_data)
            contact_data_obj.company_email = contact_data["contact_email"]
            contact_data_obj.company_number = contact_data["contact_number"]
            contact_data_obj.company_address = contact_data["contact_address"]

            contact_data_obj.save()

        if about_us:
            static_content_obj.about_us = about_us

        if terms_and_conditions:
            static_content_obj.terms_and_conditions = terms_and_conditions

        if privacy_policy:
            static_content_obj.privacy_policy = privacy_policy

        static_content_obj.save()

        if faqs:
            faqs = json.loads(faqs)
            FAQ.objects.all().delete()
            for faq in faqs:
                FAQ.objects.create(question=faq["question"], answer=faq["answer"])

        return JsonResponse({"message": "OK"})


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


class NotificationsView(ListView):
    template_name = "notifications.html"
    model = AdminNotification
    context_object_name = "notification_list"
    paginate_by = 5

    def get_queryset(self):
        return AdminNotification.objects.all()
