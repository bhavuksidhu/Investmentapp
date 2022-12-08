from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from djmoney.money import Money
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import WalletSerializer
from core.models import User, UserProfile
from wallets.forms import AddCoinsForm
from wallets.models import Wallet, WalletTransaction
from django.views.generic import ListView, CreateView


class WalletViewSetAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer = WalletSerializer
    model = Wallet


class WalletViewAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer = WalletSerializer
    model = Wallet

    def get(self, request):
        """
        Returns wallet obj of the logged-in user
        """
        user: User = Token.objects.get(user_id=request.user.pk).user
        try:
            wallet: Wallet = Wallet.objects.get(userprofile__user_id=user.pk)

            resp = {
                "wallet_id": wallet.pk,
                "balance": wallet.coin_balance.amount,
                "currency": wallet.coin_balance.currency.code,
            }
            response_code = 200
        except Wallet.DoesNotExist as exc:
            resp = {
                "message": f"Wallet for user id {user.pk} not found.",
                "errors": [str(exc)]
            }
            response_code = 404

        return Response(data=resp, status=response_code)


class WalletView(LoginRequiredMixin, ListView):
    model = Wallet
    context_object_name = "wallets"


class AddCoinsView(LoginRequiredMixin, CreateView):
    model = Wallet
    context_object_name = "wallets"
    permission_classes = (IsAdminUser,)
    form_class = AddCoinsForm
    template_name = "customer_detail.html"

    def post(self, request, *args, **kwargs):

        user_id = self.kwargs.get("pk")
        user_profile = UserProfile.objects.get(user_id=user_id)

        try:
            wallet = Wallet.objects.get(userprofile__user_id=user_id)
        except Wallet.DoesNotExist as exc:

            wallet = Wallet.objects.create(
                userprofile_id=user_profile.pk,
                coin_balance=settings.INITIAL_COIN_BALANCE
            )
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=settings.INITIAL_COIN_BALANCE,
                coin_balance=settings.INITIAL_COIN_BALANCE,
                notes="Auto-generated initial coin balance"
            )

            wallet.coin_balance = settings.INITIAL_COIN_BALANCE
            wallet.save()
            messages.info(request,
                          "User does not have a wallet. New wallet created with INR 1500.",
                          extra_tags="alert alert-info")

        form = self.form_class(data=request.POST)

        if form.is_valid():
            current_balance = wallet.coin_balance
            new_balance = current_balance + form.cleaned_data.get("amount")

            WalletTransaction.objects.create(
                wallet_id=wallet.pk,
                amount=form.cleaned_data.get("amount"),
                transaction_type="CREDIT",
                notes=f"Coins added by {request.user.email}",
                coin_balance=new_balance
            )
            wallet.coin_balance = new_balance
            wallet.save()
            messages.success(request, "Amount added successfully", extra_tags="alert alert-success")

            return redirect(to=f"/adminpanel/customer-detail/{user_id}/")
        else:
            messages.error(request, "Form errors occurred", extra_tags="alert alert-danger")
            context = {"form": self.form_class, "wallet": wallet}
            return render(request, self.template_name, context)



