from django.conf import settings

from core.models import UserProfile
from django.db.models.signals import post_save
from django.dispatch import receiver

from wallets.models import Wallet, WalletTransaction


@receiver(post_save, sender=UserProfile)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        wallet = Wallet.objects.create(
            userprofile_id=instance.pk,
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
