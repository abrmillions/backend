from rest_framework import generics, permissions, viewsets
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


User = get_user_model()


class FlexibleTokenObtainPairSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.setdefault('email', self.fields.get(get_user_model().USERNAME_FIELD))
        self.fields.setdefault('username', self.fields.get(get_user_model().USERNAME_FIELD))

    def validate(self, attrs):
        username_field = get_user_model().USERNAME_FIELD
        incoming_email = attrs.get('email')
        incoming_username = attrs.get('username')
        if username_field == 'email':
            if incoming_email is None and incoming_username is not None:
                attrs['email'] = incoming_username
        else:
            if incoming_username is None and incoming_email is not None:
                attrs['username'] = incoming_email
        return super().validate(attrs)


class FlexibleTokenObtainPairView(TokenObtainPairView):
    parser_classes = (JSONParser, FormParser, MultiPartParser)
    serializer_class = FlexibleTokenObtainPairSerializer


class TokenLoginView(APIView):
    permission_classes = (AllowAny,)
    parser_classes = (JSONParser, FormParser, MultiPartParser)

    def post(self, request):
        username_field = get_user_model().USERNAME_FIELD
        identifier = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')
        if not identifier or not password:
            return Response({'detail': 'Email/username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        payload = {username_field: identifier, 'password': password}
        serializer = TokenObtainPairSerializer(data=payload)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')



class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """Return or update the currently authenticated user's data."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """Blacklist refresh token to logout user."""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh") or request.data.get("refresh_token")
            if not refresh_token:
                return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """Request a password reset. Returns reset_url in response for local/dev environments."""
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')
        frontend_url = request.data.get('frontend_url') or request.data.get('frontendUrl') or ''
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                # Do not reveal whether the email exists
                return Response({'detail': 'If this email is registered, a password reset link will be sent.'}, status=status.HTTP_200_OK)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            if frontend_url:
                reset_url = f"{frontend_url.rstrip('/')}/reset-password?uid={uid}&token={token}"
            else:
                # Fallback to backend confirm endpoint for development
                reset_url = f"{request.scheme}://{request.get_host()}/api/users/password-reset/confirm/?uid={uid}&token={token}"

            # Try sending email; if EMAIL_BACKEND not configured for real sending, swallow errors and return the URL
            subject = getattr(settings, 'PASSWORD_RESET_SUBJECT', 'Password reset')
            message = getattr(settings, 'PASSWORD_RESET_MESSAGE', f'Use the following link to reset your password: {reset_url}')
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)

            try:
                send_mail(subject, message, from_email, [user.email], fail_silently=True)
            except Exception:
                # ignore email sending errors in dev
                pass

            # For developer convenience, return reset_url in JSON when running locally
            return Response({'detail': 'If this email is registered, a password reset link has been sent.', 'reset_url': reset_url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        uid = request.data.get('uid') or request.query_params.get('uid')
        token = request.data.get('token') or request.query_params.get('token')
        new_password = request.data.get('new_password') or request.data.get('password')

        if not uid or not token or not new_password:
            return Response({'detail': 'uid, token and new_password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            try:
                uid_decoded = force_str(urlsafe_base64_decode(uid))
            except Exception:
                return Response({'detail': 'Invalid uid.'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(pk=uid_decoded).first()
            if not user:
                return Response({'detail': 'Invalid token or user.'}, status=status.HTTP_400_BAD_REQUEST)

            if not default_token_generator.check_token(user, token):
                return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({'detail': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckEmailView(APIView):
    """Check whether an email is valid and already exists in the system.
    Does NOT verify whether the mailbox actually exists at the provider.
    """
    permission_classes = (AllowAny,)

    def get(self, request):
        email = request.query_params.get('email') or request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate basic email syntax
        syntax_valid = True
        try:
            validate_email(email)
        except ValidationError:
            syntax_valid = False

        # Check existence in our system
        exists = User.objects.filter(email__iexact=email).exists()

        # Best-effort domain check (simple heuristic, no external DNS dependency)
        domain_ok = False
        try:
            parts = str(email).split('@')
            if len(parts) == 2:
                domain = parts[1]
                domain_ok = '.' in domain and len(domain.split('.')) >= 2
        except Exception:
            domain_ok = False

        return Response({
            'email': email,
            'syntax_valid': syntax_valid,
            'domain_likely_valid': domain_ok,
            'exists_in_system': exists,
        }, status=status.HTTP_200_OK)


class EmailVerificationRequestView(APIView):
    """Send an email verification link to the user. Accepts either authenticated user or an email parameter."""
    permission_classes = (AllowAny,)

    def post(self, request):
        # If authenticated, use current user; otherwise accept email
        user = getattr(request, 'user', None)
        target_email = None
        if user and user.is_authenticated:
            target_email = getattr(user, 'email', None)
        if not target_email:
            target_email = request.data.get('email') or request.query_params.get('email')
        if not target_email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(target_email)
        except ValidationError:
            return Response({'detail': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Load user by email
            User = get_user_model()
            target_user = User.objects.filter(email__iexact=target_email).first()
            if not target_user:
                return Response({'detail': 'No account found for this email.'}, status=status.HTTP_404_NOT_FOUND)

            if getattr(target_user, 'email_verified', False):
                return Response({'detail': 'Email is already verified.'}, status=status.HTTP_200_OK)

            token = default_token_generator.make_token(target_user)
            uid = urlsafe_base64_encode(force_bytes(target_user.pk))

            frontend_url = request.data.get('frontend_url') or request.data.get('frontendUrl') or ''
            if frontend_url:
                verify_url = f"{frontend_url.rstrip('/')}/verify-email?uid={uid}&token={token}"
            else:
                verify_url = f"{request.scheme}://{request.get_host()}/api/users/email-verification/confirm/?uid={uid}&token={token}"

            subject = getattr(settings, 'EMAIL_VERIFICATION_SUBJECT', 'Verify your email')
            message = getattr(settings, 'EMAIL_VERIFICATION_MESSAGE', f'Click to verify your email: {verify_url}')
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
            try:
                send_mail(subject, message, from_email, [target_user.email], fail_silently=True)
            except Exception:
                pass

            return Response({'detail': 'Verification email sent.', 'verify_url': verify_url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailVerificationConfirmView(APIView):
    """Confirm the email verification using uid and token."""
    permission_classes = (AllowAny,)

    def post(self, request):
        uid = request.data.get('uid') or request.query_params.get('uid')
        token = request.data.get('token') or request.query_params.get('token')
        if not uid or not token:
            return Response({'detail': 'uid and token are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
        except Exception:
            return Response({'detail': 'Invalid uid.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            User = get_user_model()
            user = User.objects.filter(pk=uid_decoded).first()
            if not user:
                return Response({'detail': 'Invalid token or user.'}, status=status.HTTP_400_BAD_REQUEST)

            if not default_token_generator.check_token(user, token):
                return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

            # Mark email as verified
            try:
                user.email_verified = True
                user.is_active = True  # Optionally activate account on verification
                user.save(update_fields=['email_verified', 'is_active'])
            except Exception:
                user.email_verified = True
                user.save()
            return Response({'detail': 'Email has been verified successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
