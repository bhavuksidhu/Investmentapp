from django import forms
from djmoney.forms import MoneyField

from wallets.models import WalletTransaction


class AddCoinsForm(forms.ModelForm):
    amount = MoneyField(max_digits=25)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['amount'].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = WalletTransaction
        fields = ("amount",)
