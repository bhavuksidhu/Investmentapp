import uuid
from datetime import timedelta
from hashlib import sha512

import requests
from adminpanel.models import AdminNotification
from core.models import (
    Notification,
    User,
    UserSetting,
    UserSubscription,
    UserSubscriptionHistory,
)
from core.utils import send_notification
from django.conf import settings
from django.utils import timezone

from payment.models import PayUOrder

PAYU_CREDS_KEY = settings.PAYU_CREDS["key"]
PAYU_CREDS_SALT = settings.PAYU_CREDS["salt"]
SUBSCRIPTION_AMOUNT = settings.SUBSCRIPTION_AMOUNT

PAYU_BASE_URL = "https://secure.payu.in/_payment"
PAYU_S_RETURN_URL = f"http://{settings.HOST}/payments/success/"
PAYU_F_RETURN_URL = f"http://{settings.HOST}/payments/faliure/"


def create_order(
    user: User, amount: float = 69.0, order_note: str = "Invet-Thrift Subscription Order"
):
    order_id = str(uuid.uuid4())

    key = PAYU_CREDS_KEY
    txnid = order_id
    amount = amount
    firstname = user.profile.first_name
    email = user.email
    productinfo = "Invest Thrift Subscription"
    salt = PAYU_CREDS_SALT
    # sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)
    hash_str = (
        f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{salt}"
    )
    hash_value = sha512(str(hash_str).encode("utf-8")).hexdigest().lower()

    PayUOrder.objects.create(
        user=user,
        order_id=order_id,
        amount=amount,
        order_status="CREATED",
        hash_value=hash_value,
    )

    return order_id


def handle_subscription_update(user: User, amount: float, order_id):
    subscription: UserSubscription = user.subscription
    if subscription.date_to and subscription.date_from:
        subscription.date_to = subscription.date_to + timedelta(days=365)
    else:
        subscription.date_from = timezone.now().date()
        subscription.date_to = timezone.now().date() + timedelta(days=365)

    subscription.active = True
    subscription.save()

    history_obj = UserSubscriptionHistory.objects.create(
        subscription=subscription, amount=amount, transaction_id=str(order_id), payment_gateway="PayU"
    )
    
    AdminNotification.objects.create(
        title=f"Subscription Purchased!",
        content=f"User - CU{user.id}, has just purchased a subscription!",
    )
    try:
        registration_id = user.settings.device_token
    except UserSetting.DoesNotExist:
        print("No Settings exist for user, aborting notification service.")

    head = f"Subscription Purchased!"
    body = f"Your subscription renewal is successful."
    Notification.objects.create(
        user=user, notification_type="Subscription", head=head, body=body
    )
    if registration_id:
        send_notification(
            registration_id=registration_id, message_title=head, message_body=body
        )
    else:
        print("No device_token exist for user, aborting notification service.")


def confirm_and_update_order(order_id: str):

    url = "https://info.payu.in/merchant/postservice?form=2"
    hash_str = f"{PAYU_CREDS_KEY}|verify_payment|{order_id}|{PAYU_CREDS_SALT}"
    hash_value = sha512(str(hash_str).encode("utf-8")).hexdigest().lower()
    payload = (
        f"key={PAYU_CREDS_KEY}&command=verify_payment&var1={order_id}&hash={hash_value}"
    )
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(url, data=payload, headers=headers)

    if response.status_code == 200:
        status = response.json()["transaction_details"][order_id]["status"]
        if status == "success":
            order = PayUOrder.objects.get(order_id=order_id)
            order.order_status = "VERIFIED"
            order.save()
            amt = float(response.json()["transaction_details"][order_id]["amt"])
            handle_subscription_update(user=order.user, amount=amt, order_id=order_id)
            return True

    return False


def get_payment_context(order_id: str):

    order: PayUOrder = PayUOrder.objects.get(order_id=order_id)
    user = order.user

    key = PAYU_CREDS_KEY
    txnid = order_id
    amount = order.amount
    firstname = user.profile.first_name
    email = user.email
    productinfo = "Invest Thrift Subscription"
    salt = PAYU_CREDS_SALT
    # sha512(key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT)
    hash_str = (
        f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{salt}"
    )
    hash_value = sha512(str(hash_str).encode("utf-8")).hexdigest().lower()

    return {
        "key": key,
        "order_id": order_id,
        "product_info": productinfo,
        "amount": amount,
        "email": email,
        "first_name": firstname,
        "s_url": PAYU_S_RETURN_URL,
        "f_url": PAYU_F_RETURN_URL,
        "hash_value": hash_value,
    }
