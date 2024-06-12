from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView

from . import views


app_name = 'core'


urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='refresh-token'),
    path('otp/', views.OTPGenericAPIView.as_view(), name='otp'),
    path('otp/verify/', views.VerifyOTPGenericAPIView.as_view(), name='otp-verify')
]
