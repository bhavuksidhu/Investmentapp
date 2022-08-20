import json
import urllib.parse

import requests
from adminpanel.models import AdminNotification
from core.models import Notification, Transaction, User, UserSetting, ZerodhaData
from core.utils import send_notification
from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.views.generic import View
from drf_spectacular.utils import extend_schema, inline_serializer
from kiteconnect import KiteConnect
from rest_framework import serializers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

from api.utils import check_kyc_status

KITE_CREDS = settings.KITE_CREDS
kite = KiteConnect(api_key=KITE_CREDS["api_key"])


class Redirect(APIView):
    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="zerodha_redirect",
            fields={
                "errors": serializers.CharField(),
                "data": serializers.JSONField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def get(self, request: Request, *args, **kwargs):
        action = request.query_params.get("action", None)
        uuid = request.query_params.get("uuid", None)
        type = request.query_params.get("type", None)
        zerodha_status = request.query_params.get("status", None)
        request_token = request.query_params.get("request_token", None)

        result = "Success"
        message = "Thank you! Your transaction has been completed successfully"

        if action == "basket":
            return render(
                request, "zerodha_redirect.html", {"result": result, "message": message}
            )

        if not uuid:
            result = "Failure"
            message = "Uh oh.. KYC linking failed, Please try again!"
            return render(
                request, "zerodha_redirect.html", {"result": result, "message": message}
            )

        if zerodha_status == "cancelled":
            result = "Failure"
            message = "Uh oh.. KYC linking failed, Please try again!"
            return render(
                request, "zerodha_redirect.html", {"result": result, "message": message}
            )

        if action and type and zerodha_status and request_token:
            if zerodha_status == "success":
                data = kite.generate_session(
                    request_token, api_secret=KITE_CREDS["secret"]
                )
                kite.set_access_token(data["access_token"])

                margins_data = kite.margins()
                funds = margins_data["equity"]["available"]["cash"]

                try:
                    user: User = User.objects.get(uuid=uuid)
                    # Delete old data
                    ZerodhaData.objects.filter(local_user=user).delete()
                    # Create new data
                    data["local_user_id"] = user.id
                    data["funds"] = funds
                    data["created_at"] = timezone.now()
                    ZerodhaData.objects.create(**data)

                    result = "Success"
                    message = "Thank you! KYC linked successfully!"
                    return render(
                        request,
                        "zerodha_redirect.html",
                        {"result": result, "message": message},
                    )
                except User.DoesNotExist:
                    result = "Failure"
                    message = "Uh oh.. KYC linking failed, Please try again!"
                    return render(
                        request,
                        "zerodha_redirect.html",
                        {"result": result, "message": message},
                    )

        result = "Failure"
        message = "Uh oh.. KYC linking failed, Please try again!"
        return render(
            request, "zerodha_redirect.html", {"result": result, "message": message}
        )


class KYCView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="zerodha_kyc",
            fields={
                "errors": serializers.CharField(),
                "kyc_url": serializers.URLField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def get(self, request: Request, *args, **kwargs):
        uuid = request.user.uuid

        redirect_params = urllib.parse.quote(f"uuid={uuid}")
        redirect_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={KITE_CREDS['api_key']}&redirect_params={redirect_params}"

        return Response(
            {
                "errors": "None",
                "kyc_url": redirect_url,
                "status": status.HTTP_200_OK,
            },
            status=status.HTTP_200_OK,
        )


class CheckStatus(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="zerodha_check_status",
            fields={
                "errors": serializers.CharField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def get(self, request: Request, *args, **kwargs):
        kyc_done = check_kyc_status(user=request.user)
        if kyc_done:
            return Response(
                {
                    "errors": None,
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "errors": "KYC NOT DONE OR EXPIRED",
                    "status": status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )


class ExecuteTradeView(APIView):
    renderer_classes = (TemplateHTMLRenderer,)

    def get(self, request, *args, **kwargs):
        transaction_id = kwargs.get("transaction_id", None)
        print(transaction_id)
        if not transaction_id:
            return HttpResponseNotFound("Invalid URL or Expired!")

        try:
            transaction_id = int(transaction_id)
            transaction_obj: Transaction = Transaction.objects.get(uid=transaction_id)
        except Transaction.DoesNotExist:
            return HttpResponseNotFound("Invalid URL or Expired!")

        if transaction_obj.executed:
            return HttpResponseNotFound("Invalid URL or Expired!")

        transaction_obj.executed = True
        transaction_obj.save()

        json_data = [
            {
                "variety": "regular",
                "tradingsymbol": transaction_obj.trading_symbol,
                "exchange": transaction_obj.exchange,
                "transaction_type": transaction_obj.transaction_type.upper(),
                "order_type": "MARKET",
                "quantity": transaction_obj.quantity,
                "readonly": True,
                "tag": f"{transaction_obj.id}",
            }
        ]

        api_key = KITE_CREDS["api_key"]

        return Response(
            {"json_data": json.dumps(json_data), "api_key": api_key},
            template_name="zerodha/execute-trade.html",
        )


class RefreshFundsView(APIView):
    serializer_class = None
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="zerodha_refresh_funds",
            fields={
                "errors": serializers.CharField(),
                "funds": serializers.FloatField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def get(self, request, *args, **kwargs):
        api_key = KITE_CREDS["api_key"]

        try:
            zerodha_data: ZerodhaData = request.user.zerodha_data
            access_token = zerodha_data.access_token
        except ZerodhaData.DoesNotExist:
            return Response(
                {
                    "errors": "KYC NOT DONE OR EXPIRED",
                    "funds": None,
                    "status": status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {api_key}:{access_token}",
        }
        resp = requests.get("https://api.kite.trade/user/margins", headers=headers)
        if resp.status_code != 200:
            return Response(
                {
                    "errors": "KYC NOT DONE OR EXPIRED",
                    "funds": None,
                    "status": status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            current_funds = resp.json()["data"]["equity"]["available"]["cash"]
            zerodha_data.funds = current_funds
            zerodha_data.save()
            return Response(
                {
                    "errors": None,
                    "funds": current_funds,
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )


class PostBackView(APIView):
    def post(self, request, *args, **kwargs):

        data = json.loads(request.body)
        # if not os.path.isdir("postbacks"):
        #     os.mkdir("postbacks")
        # with open(os.path.join("postbacks",f"{str(uuid.uuid4())}.json"),"w", encoding="utf-8") as f:
        #     json.dump(data,f,ensure_ascii=False)

        tag = data.get("tag", None)
        if not tag:
            return Response(data={"msg": "No Tag"}, status=200)
        tag = int(tag)
        try:
            transaction_obj: Transaction = Transaction.objects.get(id=tag)
        except Transaction.DoesNotExist:
            return Response(data={"msg": "No Transaction Obj"}, status=200)

        if data.get("status", None) == "COMPLETE":
            transaction_obj.price = data.get("average_price")
            transaction_obj.quantity = data.get("quantity")
            transaction_obj.amount = transaction_obj.price * transaction_obj.quantity
            transaction_obj.verified = True
            transaction_obj.status = "Completed"
            transaction_obj.zerodha_postback = data

            AdminNotification.objects.create(
                notification_type="TRADE",
                title=f"New trade!",
                content=f"A new trade just took place, ID : ORD{transaction_obj.id}.",
            )

            user = transaction_obj.user
            notification_type = (
                "Purchase" if transaction_obj.transaction_type == "BUY" else "Sale"
            )
            head = f"{notification_type} Complete!"
            body = f"Your {notification_type.lower()} order for {transaction_obj.trading_symbol} was completed successfully!"
            Notification.objects.create(
                user=user, notification_type=notification_type, head=head, body=body
            )

            try:
                registration_id = user.settings.device_token
            except UserSetting.DoesNotExist:
                print("No Settings exist for user, aborting notification service.")

            if registration_id:
                send_notification(
                    registration_id=registration_id,
                    message_title=head,
                    message_body=body,
                )
            else:
                print("No device_token exist for user, aborting notification service.")

        else:
            transaction_obj.status = data.get("status", "Cancelled").title()
            transaction_obj.zerodha_postback = data
        transaction_obj.save()

        return Response(data={"msg": "Done"}, status=200)
