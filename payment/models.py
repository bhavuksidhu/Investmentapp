from django.db import models
from core.models import User

# Create your models here.
class PayUOrder(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="payu_orders"
    )
    order_id = models.UUIDField()
    amount = models.FloatField()
    order_status = models.TextField()
    hash_value = models.TextField()

    json = models.JSONField(null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
