from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken as DefaultObtainAuthToken
from .serializers import CustomUserSerializer, CustomAuthTokenSerializer, AdminUserSerializer, UserProfileUpdateSerializer, PasswordChangeSerializer
from django.contrib.auth import login, logout, update_session_auth_hash
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware import csrf
from ..models import CustomUser

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

class CustomObtainAuthToken(DefaultObtainAuthToken):
    """
    Custom token authentication view that uses our custom serializer.
    This allows the API to explicitly expect 'custom_id' instead of 'username'.
    """
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # Start a session upon successful authentication
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            user_data = CustomUserSerializer(user).data
            return Response({
                'token': token.key,
                'user': user_data
            })
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
    is_expired = getattr(request.user, 'is_password_expired', False)
    return JsonResponse({
        'isAuthenticated': True,
        'isStaff': request.user.is_staff,
        'isSuperuser': request.user.is_superuser,
        'username': request.user.username,
        'isPasswordExpired': is_expired,
    })

class UserSettingsDetailView(APIView):
    """
    API endpoint for retrieving and updating the authenticated user's profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Return the current user's profile data.
        """
        user = request.user
        # Use the AdminUserSerializer to include fields like is_staff
        serializer = AdminUserSerializer(user)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Update the current user's profile.
        """
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(AdminUserSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPasswordChangeView(APIView):
    """
    API endpoint for changing the user's password.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password1'])
            user.save()
            # To keep the user logged in after password change
            update_session_auth_hash(request, user)
            return Response({'message': 'パスワードが正常に変更されました。'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APITokenView(APIView):
    """
    API endpoint for retrieving and regenerating the user's API token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        token, _ = Token.objects.get_or_create(user=request.user)
        token.delete()
        new_token = Token.objects.create(user=request.user)
        return Response({'message': 'APIトークンが再生成されました。', 'api_token': new_token.key})

class IsStaffOrSuperuser(permissions.BasePermission):
    """
    Allows access only to staff or superusers.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.is_staff or request.user.is_superuser)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    Accessible only by staff members.
    """
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrSuperuser]