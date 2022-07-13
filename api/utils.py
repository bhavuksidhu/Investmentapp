from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination

from core.models import User, ZerodhaData
from django.utils import timezone


def parse_serializer_errors(serializer):
    return " ".join("".join(x).title() for e, x in serializer.errors.items())

def check_kyc_status(user: User):
    try:
        zerodha_data: ZerodhaData = ZerodhaData.objects.get(local_user=user)
    except ZerodhaData.DoesNotExist:
        return False

    if not zerodha_data.login_time:
        return False

    if timezone.localtime().day == zerodha_data.login_time.day:
        return True
    else:
        return False


class NoDataException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {
        "status": status.HTTP_404_NOT_FOUND,
        "message": "No data is available",
    }


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_query_param = "page"

PAN_REGEX = r"[A-Za-z]{5}\d{4}[A-Za-z]{1}"
