from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from wallets.models import Wallet, WalletTransaction
from django.views.generic import ListView


class WalletView(LoginRequiredMixin, ListView):
    model = Wallet
    context_object_name = "wallets"


