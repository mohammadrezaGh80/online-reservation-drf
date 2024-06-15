from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action

from .serializers import OTPSerializer, VerifyOTPSerializer, UserSerializer, UserDetailSerializer, SetPasswordSerializer
from .throttles import RequestOTPThrottle
from .models import OTP
from .paginations import CustomLimitOffsetPagination


User = get_user_model()


class OTPGenericAPIView(generics.GenericAPIView):
    serializer_class = OTPSerializer

    def get_throttles(self):
        if self.request.method == 'POST':
            return [RequestOTPThrottle()]
        return []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True) 
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyOTPGenericAPIView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            phone = validated_data.get('phone')
            password = validated_data.get('password')
            request_id = validated_data.get('id')

            try:
                otp_obj = OTP.objects.get(
                    id=request_id,
                    phone=phone,
                    password=password,
                    expired_datetime__gte=timezone.now(),
                )

                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    user = User(phone=phone)
                    user.set_unusable_password()
                    user.save()
                
                otp_obj.delete()

                refresh_token = RefreshToken.for_user(user=user)
                return Response({
                        'refresh': str(refresh_token),
                        'access': str(refresh_token.access_token), 
                        'user_id': user.id,
                        'phone': user.phone,
                    }, status=status.HTTP_200_OK)
            
            except OTP.DoesNotExist:
                return Response({'detail': _('Your one-time password is incorrect or has expired!')}, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(ModelViewSet):
    queryset = User.objects.order_by('-id')
    pagination_class = CustomLimitOffsetPagination
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return UserSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return UserDetailSerializer
    

    @action(detail=True, methods=['POST'])
    def set_password(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': _("User's password has been successfully changed.")}, status=status.HTTP_200_OK)
