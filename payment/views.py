from django.conf import settings
from django.shortcuts import render

from payment.models import PayUOrder
from payment.utils import confirm_and_update_order, create_order, get_payment_context

PAYU_CREDS_KEY = settings.PAYU_CREDS["key"]
PAYU_CREDS_SALT = settings.PAYU_CREDS["salt"]

from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class SubscribeView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=None,
        responses=inline_serializer(
            name="add_amount_response",
            fields={
                "checkout_url": serializers.URLField(),
                "errors": serializers.CharField(),
                "status": serializers.IntegerField(),
            },
        ),
    )
    def post(self, request: Request, *args, **kwargs):
        amount = 1.0
        order_id = create_order(request.user, amount)
        payment_link = f"http://{settings.HOST}/payments/subscribe/?order_id={order_id}"
        return Response(
            {
                "checkout_url": payment_link,
                "errors": None,
                "status": status.HTTP_200_OK,
            }
        )

class CheckOutView(APIView):
    failure_template_name = "failure.html"
    payu_template_name = "payu_payment.html"

    def get(self, request: Request, *args, **kwargs):
        context = {}
        order_id = request.query_params.get("order_id",None)
        if not order_id:
            return render(request, self.failure_template_name, context=context)
        
        #Build context and render payu.html
        context = get_payment_context(order_id)
        return render(request, self.payu_template_name, context=context)


class SuccessView(APIView):
    success_template_name = "success-message.html"
    failure_template_name = "failure.html"

    def post(self, request: Request, *args, **kwargs):
        print(request.data)

        context = {}
        order_id = request.data.get("txnid",None)
        if not order_id:
            return render(request, self.failure_template_name, context=context)
        try:
            order = PayUOrder.objects.get(order_id = order_id)
        except PayUOrder.DoesNotExist:
            return render(request, self.failure_template_name, context=context)
        
        if order.order_status == "VERIFIED":
            return render(request, self.failure_template_name, context=context)

        response_json = dict(request.data)
        order.json = response_json
        order.save()
        if confirm_and_update_order(order_id):
            return render(request, self.success_template_name, context=context)
        else:
            return render(request, self.failure_template_name, context=context)


class FaliureView(APIView):
    failure_template_name = "failure.html"

    def post(self, request: Request, *args, **kwargs):
        print(request.data)
        context = {}
        order_id = request.data.get("txnid",None)
        if not order_id:
            return render(request, self.failure_template_name, context=context)
        try:
            order = PayUOrder.objects.get(order_id = order_id)
        except PayUOrder.DoesNotExist:
            return render(request, self.failure_template_name, context=context)
        
        order.order_status = "FAILED"
        response_json = dict(request.data)
        order.json = response_json
        order.save()
        return render(request, self.failure_template_name, context=context)
