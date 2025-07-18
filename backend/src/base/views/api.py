from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings

class AppInfoView(APIView):
    """
    アプリケーションの基本情報を提供します。
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """
        アプリケーションのバージョンなどの情報を返します。
        """
        app_info = {
            'version': settings.VERSION,
        }
        return Response(app_info)