from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from invest.settings import DEFAULT_CURRENCY


class Wallet(models.Model):
    userprofile = models.ForeignKey(to='core.UserProfile', on_delete=models.DO_NOTHING)
    coin_balance = MoneyField(max_digits=14, decimal_places=2, default_currency='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.userprofile.last_name} bal. {self.coin_balance}"

    class Meta:
        ordering = ("-created_at",)


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("DEBIT", "Debit"), ("CREDIT", "Credit"),
        ("REFUND", "Refund"), ("UNDEFINED", "Undefined")
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.DO_NOTHING)
    transaction_type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = MoneyField(default=Money(0.00, DEFAULT_CURRENCY), max_digits=25)
    coin_balance = MoneyField(default=Money(0.00, DEFAULT_CURRENCY), max_digits=25)
    notes = models.TextField(max_length=500)
    date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} amount {self.amount}"


