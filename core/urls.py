from django.urls import path
from rest_framework_simplejwt.views import  TokenRefreshView
from rest_framework.routers import DefaultRouter

from . import views


app_name = 'core'


router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')


urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='refresh-token'),
    path('otp/', views.OTPGenericAPIView.as_view(), name='otp'),
    path('otp/verify/', views.VerifyOTPGenericAPIView.as_view(), name='otp-verify'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
] + router.urls
