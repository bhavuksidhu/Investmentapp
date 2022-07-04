from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination


def parse_serializer_errors(serializer):
    return " ".join("".join(x).title() for e, x in serializer.errors.items())


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
