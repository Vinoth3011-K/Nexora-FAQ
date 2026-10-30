import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer

logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Registration validation failed.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        tokens = get_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        return Response({
            'status': 'success',
            'message': 'Account registered successfully.',
            'tokens': tokens,
            'user': user_data,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            error_message = "Invalid email address or password."
            non_field_errors = serializer.errors.get('non_field_errors')
            if non_field_errors:
                error_message = str(non_field_errors[0])
            elif serializer.errors:
                first_field = next(iter(serializer.errors))
                error_message = str(serializer.errors[first_field][0])

            return Response({
                'status': 'error',
                'message': error_message,
                'errors': serializer.errors,
            }, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        user_data = UserProfileSerializer(user).data

        return Response({
            'status': 'success',
            'message': 'Login successful.',
            'tokens': tokens,
            'user': user_data,
        }, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user)
        return Response({
            'status': 'success',
            'user': serializer.data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        return Response({
            'status': 'success',
            'message': 'Logged out successfully.',
        }, status=status.HTTP_200_OK)
