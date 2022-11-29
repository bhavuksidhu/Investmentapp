import json
from datetime import datetime, timedelta

import pandas as pd
from rest_framework.authtoken.models import Token

from core.models import (
    MarketQuote,
    Stock,
    Transaction,
    User,
    UserProfile,
    UserSubscription,
    UserSubscriptionHistory,
)
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
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
    Tip,
)
from adminpanel.utils import send_tip_notification


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
                        messages.add_message(
                            request, messages.SUCCESS, "Logged in Successfully!"
                        )
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
        messages.add_message(request, messages.SUCCESS, "Logged out Successfully!")
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


class DashboardView(LoginRequiredMixin, View):
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
        context["total_subscribed_users"] = user_query.filter(subscription__active=True).count()
        context["from_period"] = from_period
        context["from_date"] = from_date
        context["to_date"] = to_date
        context["today_date"] = datetime.today().strftime("%Y-%m-%d")
        context["header"] = header

        return render(
            request,
            self.template,
            context=context,
        )


class CustomerManagementView(LoginRequiredMixin, ListView):
    template_name = "customer_management.html"
    model = User
    context_object_name = "user_list"
    paginate_by = 15

    def get_queryset(self):
        q = self.request.GET.get("q", None)
        if q:
            q = q.strip()
            if "CU" in q:
                try:
                    user_id = int(q.replace("CU", ""))
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


class CustomerDetailView(LoginRequiredMixin, View):
    template_name = "customer_detail.html"
    mode = User

    def get_data(self):
        q = self.request.GET.get("q", None)
        user = User.objects.select_related("profile").get(id=self.kwargs.get("pk"))

        base_transaction_query = user.transactions.filter(verified=True)

        # Transactions Section
        transactions_query = base_transaction_query
        transaction_from_date = self.request.GET.get("transaction_from_date", None)
        transaction_to_date = self.request.GET.get("transaction_to_date", None)
        if transaction_from_date:
            transactions_query = transactions_query.filter(
                created_at__date__gte=transaction_from_date
            )
        if transaction_to_date:
            transactions_query = transactions_query.filter(
                created_at__date__lte=transaction_to_date
            )

        if q:
            q = q.strip().lower()
            if "ord" in q:
                try:
                    transaction_id = int(q.replace("ord", ""))
                    transactions_query = transactions_query.filter(id=transaction_id)
                except:
                    pass

        # Journal Section
        journals_query = base_transaction_query.filter(transaction_type="BUY")
        journal_from_date = self.request.GET.get("journal_from_date", None)
        journal_to_date = self.request.GET.get("journal_to_date", None)
        if journal_from_date:
            journals_query = journals_query.filter(
                created_at__date__gte=journal_from_date
            )
        if journal_to_date:
            journals_query = journals_query.filter(
                created_at__date__lte=journal_to_date
            )

        transactions = transactions_query
        journal = journals_query

        return {"user": user, "transactions": transactions, "journal": journal}

    def get_context_data(self, **kwargs):
        context = {}

        transaction_from_date = self.request.GET.get("transaction_from_date", None)
        transaction_to_date = self.request.GET.get("transaction_to_date", None)
        journal_from_date = self.request.GET.get("journal_from_date", None)
        journal_to_date = self.request.GET.get("journal_to_date", None)

        active_tab = self.request.GET.get("active_tab", "personal")
        q = self.request.GET.get("q", "")

        context["q"] = q
        context["transaction_from_date"] = transaction_from_date
        context["transaction_to_date"] = transaction_to_date
        context["journal_from_date"] = journal_from_date
        context["journal_to_date"] = journal_to_date
        context["active_tab"] = active_tab
        context["today_date"] = datetime.today().strftime("%Y-%m-%d")

        return context

    def get(self, request, *args, **kwagrs):
        data = self.get_data()
        context = self.get_context_data(**kwagrs)
        context["user"] = data["user"]
        context["transactions"] = data["transactions"]
        context["journal"] = data["journal"]

        return render(request, self.template_name, context=context)


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
        date_of_birth = request.POST.get("date_of_birth", None)
        gender = request.POST.get("gender", None)
        address = request.POST.get("address", None)

        try:
            user: User = User.objects.get(id=self.kwargs.get("pk"))
            profile: UserProfile = user.profile
        except User.DoesNotExist:
            return self.get(self, request, *args, **kwargs)

        if first_name:
            profile.first_name = first_name
        if last_name:
            profile.last_name = last_name
        if date_of_birth:
            profile.date_of_birth = date_of_birth
        if gender:
            profile.gender = gender
        if address:
            profile.address = address

        try:
            profile.save()
            user.save()
            messages.add_message(
                request, messages.SUCCESS, "Details updated successfully!"
            )
        except Exception as e:
            print(e)

        return redirect("adminpanel:customer-detail", self.kwargs.get("pk"))


class InvestingReportView(LoginRequiredMixin, ListView):
    template_name = "investing_reports.html"
    model = Transaction
    context_object_name = "transaction_list"
    paginate_by = 15

    def get_queryset(self):
        q = self.request.GET.get("q", None)

        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)

        query = Transaction.objects.select_related("user__profile").filter(
            verified=True
        )

        if from_date:
            query = query.filter(created_at__date__gte=from_date)
        if to_date:
            query = query.filter(created_at__date__lte=to_date)

        if q:
            q = q.strip().lower()
            if "ord" in q:
                try:
                    transaction_id = int(q.replace("ord", ""))
                    query = query.filter(id=transaction_id)
                except:
                    pass

        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["from_date"] = self.request.GET.get("from_date", None)
        context["to_date"] = self.request.GET.get("to_date", None)
        context["today_date"] = datetime.today().strftime("%Y-%m-%d")
        return context


class SubscriptionManagementView(LoginRequiredMixin, ListView):
    template_name = "subscription_management.html"
    model = UserSubscriptionHistory
    context_object_name = "subscriptions"
    paginate_by = 15

    def get_queryset(self):
        q = self.request.GET.get("q", None)

        from_date = self.request.GET.get("from_date", None)
        to_date = self.request.GET.get("to_date", None)

        query = UserSubscriptionHistory.objects.select_related()

        if from_date:
            query = query.filter(created_at__gte=from_date)
        if to_date:
            query = query.filter(created_at__lte=to_date)

        if q and "CU" in q:
            q = int(q.replace("CU", "").strip())
            query = query.filter(subscription__user__id=q)
        elif q:
            query = query.filter(
                Q(subscription__user__email__icontains=q)
                | Q(subscription__user__phone_number__icontains=q)
                | Q(subscription__user__profile__first_name__icontains=q)
            )

        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["from_date"] = self.request.GET.get("from_date", None)
        context["to_date"] = self.request.GET.get("to_date", None)
        context["today_date"] = datetime.today().strftime("%Y-%m-%d")
        return context


class StockManagementView(LoginRequiredMixin, ListView):
    template_name = "stock_management.html"
    model = Stock
    context_object_name = "stocks"
    paginate_by = 15

    def get_queryset(self):
        q = self.request.GET.get("q", None)
        query = Stock.objects.all()
        if q:
            q = q.strip()
            query = query.filter(Q(symbol__icontains=q))
        return query

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class StockUploadView(LoginRequiredMixin, View):
    template_name = "stock_upload.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):

        if not request.FILES.get("stock_file"):
            messages.add_message(request, messages.ERROR, "No file was uploaded!")
            return redirect("adminpanel:stock-upload")

        df = pd.read_excel(request.FILES.get("stock_file"))
        if "symbol" not in df or df["symbol"].isnull().values.any():
            messages.add_message(
                request, messages.ERROR, "Symbol columns can't be empty!"
            )
            return redirect("adminpanel:stock-upload")

        Stock.objects.all().delete()
        df = df.fillna("")
        [Stock.objects.create(**x) for x in df.T.to_dict().values()]

        stocks = Stock.objects.all()

        for stock in stocks:
            try:
                market_quote: MarketQuote = MarketQuote.objects.get(
                    trading_symbol=stock.symbol
                )
                market_quote.extra_text = stock.extra_text
                market_quote.save()
            except MarketQuote.DoesNotExist:
                MarketQuote.objects.create(
                    company_name=stock.company_name,
                    trading_symbol=stock.symbol,
                    exchange="NSE",
                    price=0.0,
                    extra_text=stock.extra_text,
                )

        # Delete leftover stocks
        new_symbols = [stock.symbol for stock in stocks]
        market_quotes = MarketQuote.objects.all()
        for quote in market_quotes:
            if quote.trading_symbol not in new_symbols:
                quote.delete()

        messages.add_message(
            request, messages.SUCCESS, "Stock-list uploaded successfully!"
        )
        return redirect("adminpanel:stock-management")


class StockUploadTemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwagrs):
        return FileResponse(open("stocks_template.xlsx", "rb"))


class StockEditView(LoginRequiredMixin, DetailView):
    template_name = "stock_edit.html"
    mode = Stock
    context_object_name = "stock"

    def get_queryset(self):
        return Stock.objects.filter(id=self.kwargs.get("pk"))

    def post(self, request, *args, **kwargs):
        company_name = request.POST.get("company_name", None)
        series = request.POST.get("series", "")
        extra_text = request.POST.get("extra_text", "")

        try:
            stock: Stock = Stock.objects.get(id=self.kwargs.get("pk"))
        except Stock.DoesNotExist:
            return self.get(self, request, *args, **kwargs)

        stock.company_name = company_name
        stock.series = series
        stock.extra_text = extra_text
        stock.save()

        quote: MarketQuote = MarketQuote.objects.get(trading_symbol=stock.symbol)
        quote.extra_text = extra_text
        quote.save()

        return redirect("adminpanel:stock-management")


class StaticContentManagementView(LoginRequiredMixin, View):
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

            try:
                validate_email(contact_data["contact_email"])
            except ValidationError:
                messages.add_message(request, messages.ERROR, "Invalid email")
                return JsonResponse({"message": "OK"})

            contact_data_obj.company_email = contact_data["contact_email"].lower()
            contact_data_obj.company_number = contact_data["contact_number"]
            contact_data_obj.company_address = contact_data["contact_address"]
            contact_data_obj.website = contact_data["contact_website"]

            contact_data_obj.save()

        if about_us:
            static_content_obj.about_us = about_us
        else:
            messages.add_message(request, messages.ERROR, "About Us can't be empty!")
            return JsonResponse({"message": "OK"})

        if terms_and_conditions:
            static_content_obj.terms_and_conditions = terms_and_conditions
        else:
            messages.add_message(
                request, messages.ERROR, "Terms & Conditions can't be empty!"
            )
            return JsonResponse({"message": "OK"})

        if privacy_policy:
            static_content_obj.privacy_policy = privacy_policy
        else:
            messages.add_message(
                request, messages.ERROR, "Privacy Policy can't be empty!"
            )
            return JsonResponse({"message": "OK"})

        static_content_obj.save()

        if faqs:
            faqs = json.loads(faqs)
            for faq in faqs:
                if not faq["question"] or not faq["answer"]:
                    messages.add_message(
                        request, messages.ERROR, "FAQ Question/Answer cannot be empty!"
                    )
                    return JsonResponse({"message": "OK"})

            FAQ.objects.all().delete()
            for faq in faqs:
                FAQ.objects.create(question=faq["question"], answer=faq["answer"])

        return JsonResponse({"message": "OK"})


class SettingsView(LoginRequiredMixin, View):
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
                    return redirect("adminpanel:dashboard")
                else:
                    messages.add_message(request, messages.ERROR, "Wrong old password.")
        else:
            messages.add_message(
                request, messages.ERROR, "Password & New Password must be supplied."
            )

        return render(request, self.template)


class NotificationsView(LoginRequiredMixin, ListView):
    template_name = "notifications.html"
    model = AdminNotification
    context_object_name = "notification_list"
    paginate_by = 5

    def get_queryset(self):
        return AdminNotification.objects.all()


class TipManagementView(LoginRequiredMixin, ListView):
    template_name = "tip_management.html"
    model = Tip
    context_object_name = "tip_list"
    paginate_by = 15

    def get_queryset(self):
        q = self.request.GET.get("q", None)
        if q:
            q = q.strip()
            return Tip.objects.filter(Q(text__icontains=q))
        else:
            return Tip.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", None)
        return context

    def post(self, request, *args, **kwargs):
        todo = request.POST.get("todo", None)
        selected_id = request.POST.get("selected_id", None)

        print(todo, selected_id)

        if todo and selected_id:
            try:
                tip: Tip = Tip.objects.get(id=int(selected_id))
                if tip.is_active:
                    messages.add_message(
                        request, messages.ERROR, "You cannot delete an active tip!"
                    )
                    return JsonResponse({"message": "OK"})
                if todo == "delete":
                    tip.delete()
                if todo == "activate":
                    Tip.objects.all().update(is_active=False)
                    tip.is_active = True
                    tip.save()
                    send_tip_notification(tip.text)
            except Tip.DoesNotExist:
                return JsonResponse({"message": "Failed to find tip"})

        return JsonResponse({"message": "OK"})


class TipEditView(LoginRequiredMixin, DetailView):
    template_name = "tip_edit.html"
    mode = Tip
    context_object_name = "tip"

    def get_queryset(self):
        return Tip.objects.filter(id=self.kwargs.get("pk"))

    def post(self, request, *args, **kwargs):
        tip_text = request.POST.get("tip_text", None)

        try:
            tip: Tip = Tip.objects.get(id=self.kwargs.get("pk"))
        except Tip.DoesNotExist:
            return self.get(self, request, *args, **kwargs)

        tip.text = tip_text
        tip.save()
        return redirect("adminpanel:tip-management")


class TipAddView(LoginRequiredMixin, View):
    template_name = "tip_add.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        tip_text = request.POST.get("tip_text", None)
        Tip.objects.all().update(is_active=False)
        Tip.objects.create(text=tip_text, is_active=True)
        send_tip_notification(tip_text)
        return redirect("adminpanel:tip-management")
