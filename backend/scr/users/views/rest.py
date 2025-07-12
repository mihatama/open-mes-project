from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.authtoken.models import Token # Import Token model
from .serializers import CustomUserSerializer

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