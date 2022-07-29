import urllib.parse

from core.models import Transaction, User, ZerodhaData
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseForbidden
from drf_spectacular.utils import extend_schema, inline_serializer
from kiteconnect import KiteConnect
from rest_framework import serializers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer
import os
import uuid
from api.utils import check_kyc_status

from .custom_views import ZerodhaView
import json

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

        if action == "basket":
            data = kite.generate_session(
                    request_token, api_secret=KITE_CREDS["secret"]
                )
            return Response(
                {
                    "errors": None,
                    "data": data,
                    "status": status.HTTP_200_OK,
                },
                status=status.HTTP_200_OK,
            )

        if not uuid:
            return Response(
                {
                    "errors": "KYC linking Failed!",
                    "data": None,
                    "status": status.HTTP_401_UNAUTHORIZED,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if zerodha_status == "cancelled":
            return Response(
                {
                    "errors": "Zerodha Auth Failed",
                    "data": None,
                    "status": status.HTTP_401_UNAUTHORIZED,
                },
                status=status.HTTP_401_UNAUTHORIZED,
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
                    ZerodhaData.objects.create(**data)

                    return Response(
                        {
                            "errors": "OK",
                            "data": data,
                            "status": status.HTTP_200_OK,
                        },
                        status=status.HTTP_200_OK,
                    )
                except User.DoesNotExist:
                    return Response(
                        {
                            "errors": "Zerodha Auth Failed",
                            "data": None,
                            "status": status.HTTP_401_UNAUTHORIZED,
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )

            return Response(
                {
                    "errors": "Zerodha Auth Failed",
                    "data": None,
                    "status": status.HTTP_401_UNAUTHORIZED,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "errors": "Improper Request",
                "data": None,
                "status": status.HTTP_400_BAD_REQUEST,
            },
            status=status.HTTP_400_BAD_REQUEST,
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

        json_data = [{
            "variety": "regular",
            "tradingsymbol": transaction_obj.trading_symbol,
            "exchange": transaction_obj.exchange,
            "transaction_type": transaction_obj.transaction_type.upper(),
            "order_type": "MARKET",
            "quantity": transaction_obj.quantity,
            "readonly": True,
            "tag" : f"{transaction_obj.id}"
        }]

        api_key = KITE_CREDS["api_key"]

        return Response({"json_data":json.dumps(json_data),"api_key":api_key}, template_name="zerodha/execute-trade.html")

class PostBackView(APIView):

    def post(self, request, *args, **kwargs):

        tag = request.data.get("tag",None)
        if not tag:
            return Response(data={"msg":"No Tag"}, status=200)
        tag = int(tag)
        try:
            transaction_obj : Transaction = Transaction.objects.get(id = tag)
        except Transaction.DoesNotExist:
            return Response(data={"msg":"No Transaction Obj"}, status=200)
        
        if request.data.get("status",None) == "COMPLETE":
            transaction_obj.verified = True
            transaction_obj.status = "Completed"
            transaction_obj.save()
        if not os.path.isdir("postbacks"):
            os.mkdir("postbacks")
        with open(os.path.join("postbacks",f"{str(uuid.uuid4())}.json"),"w", encoding="utf-8") as f:
            json.dump(request.data,f,ensure_ascii=False)
        
        return Response(data={"msg":"Done"}, status=200)