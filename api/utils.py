import uuid

import requests
from core.models import User, ZerodhaData
from django.conf import settings
from django.utils import timezone
from kiteconnect import KiteConnect
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination

KITE_CREDS = settings.KITE_CREDS


def parse_serializer_errors(serializer):
    return " ".join("".join(x).title() for e, x in serializer.errors.items())


def check_kyc_status(user: User):
    try:
        zerodha_data: ZerodhaData = ZerodhaData.objects.get(local_user=user)
        access_token = zerodha_data.access_token
    except ZerodhaData.DoesNotExist:
        return False

    api_key = KITE_CREDS["api_key"]

    headers = {
        "X-Kite-Version": "3",
        "Authorization": f"token {api_key}:{access_token}",
    }
    resp = requests.get("https://api.kite.trade/user/margins", headers=headers)
    if resp.status_code != 200:
        return refresh_access_token(zerodha_data)
    return True


def refresh_access_token(zerodha_data: ZerodhaData):
    try:
        kite = KiteConnect(api_key=KITE_CREDS["api_key"])
        kite.set_access_token(zerodha_data.access_token)
        resp = kite.renew_access_token(
            refresh_token=zerodha_data.refresh_token, api_secret=KITE_CREDS["secret"]
        )
        zerodha_data.access_token = resp["access_token"]
        zerodha_data.save()
        return True
    except Exception as e:
        print(e)
        return False


def uuid_to_alphanumeric():
    return str(uuid.uuid4()).replace("-", "")[:20]


class NoDataException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {
        "status": status.HTTP_404_NOT_FOUND,
        "message": "No data is available",
    }


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 500
    page_query_param = "page"


PAN_REGEX = r"[A-Za-z]{5}\d{4}[A-Za-z]{1}"


def preprocessing_filter_spec(endpoints):
    filtered = []
    excluded_path = [
        "/zerodha/redirect",
        "/zerodha/execute-trade",
        "/zerodha/post-back",
        "verify/email/",
    ]
    for (path, path_regex, method, callback) in endpoints:
        # Remove all but DRF API endpoints
        if not any([x for x in excluded_path if x in path]):
            filtered.append((path, path_regex, method, callback))
    return filtered
