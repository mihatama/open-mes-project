from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token # Import Token model
from .serializers import CustomUserSerializer
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie


@api_view(['POST'])
def register_user(request):
    serializer = CustomUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save() # serializer.save() returns the created user instance
        token, created = Token.objects.get_or_create(user=user) # Get or create token
        return Response({
            'message': 'ユーザー登録が完了しました',
            'token': token.key # Include token in the response
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APILogoutView(APIView):
    """
    APIリクエスト用に、ユーザーをログアウトさせてJSONレスポンスを返すビュー。
    認証済みのユーザーのみがアクセスできます。
    セッションとAPIトークンの両方を無効化します。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # ユーザーに関連付けられたトークンを安全に削除します。
        try:
            # ユーザーに関連付けられたトークンを取得して削除します。
            Token.objects.get(user=request.user).delete()
        except Token.DoesNotExist:
            # トークンが存在しない場合は何もしません (セッション認証のみでログインしている場合など)。
            pass

        # Djangoのセッションを無効化します
        logout(request)
        
        return Response({'success': True, 'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ensure_csrf_cookie
def get_session_info(request):
    """
    現在のセッション情報を返し、CSRFクッキーを保証するビュー。
    """
    return JsonResponse({
        'isAuthenticated': True,
        'isStaff': request.user.is_staff,
        'isSuperuser': request.user.is_superuser,
        'username': request.user.username,
    })