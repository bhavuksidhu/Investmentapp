from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.utils import check_kyc_status

class ZerodhaView(APIView):
    
    def dispatch(self, request, *args , **kwargs ):
        if not check_kyc_status(request.user):
            return Response(
                {
                    "errors": "KYC NOT DONE OR EXPIRED",
                    "status": status.HTTP_403_FORBIDDEN,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().dispatch(request, *args, **kwargs)