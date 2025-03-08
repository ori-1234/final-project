from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import LoginHistory
from .serializers import UserSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint that validates credentials and returns an auth token
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': 'Please provide both username and password'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if not user:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Create or get auth token
    token, _ = Token.objects.get_or_create(user=user)
    
    # Log the login attempt
    LoginHistory.objects.create(
        user=user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    # Serialize user data
    serializer = UserSerializer(user)

    return Response({
        'token': token.key,
        'user': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - invalidate the token
    """
    if request.auth:
        request.auth.delete()
    return Response({'message': 'Successfully logged out'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Get current user's profile
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
