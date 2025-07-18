from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

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

class HealthCheckView(APIView):
    """
    アプリケーションのヘルスチェックを行います。
    データベース接続も確認します。
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # データベース接続を確認
        try:
            connections['default'].cursor()
            db_ok = True
        except OperationalError:
            db_ok = False

        if db_ok:
            return Response({"status": "ok", "database": "ok"})
        else:
            # サービスが利用不可であることを示す 503 を返す
            return Response({"status": "error", "database": "error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)