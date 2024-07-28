from django.urls import path
from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from . import views


app_name = 'online_reservation'


router = DefaultRouter()
router.register('provinces', views.ProvinceViewSet, basename='province')
router.register('insurances', views.InsuranceViewSet, basename='insurance')
router.register('specialties', views.SpecialtyViewSet, basename='specialty')
router.register('patients', views.PatientViewSet, basename='patient')
router.register('doctors', views.DoctorViewSet, basename='doctor')
router.register('list-waiting-comments', views.CommentListWaitingViewSet, basename='list-waiting-comments')

provinces_router = routers.NestedDefaultRouter(router, 'provinces', lookup='province')
provinces_router.register('cities', views.CityViewSet, basename='province-cities')

patients_router = routers.NestedDefaultRouter(router, 'patients', lookup='patient')
patients_router.register('reserves', views.ReservePatientViewSet, basename='patient-reserves')

doctors_router = routers.NestedDefaultRouter(router, 'doctors', lookup='doctor')
doctors_router.register('comments', views.CommentViewSet, basename='doctor-comments')
doctors_router.register('reserves', views.ReserveDoctorViewSet, basename='doctor-reserves')

urlpatterns = router.urls + provinces_router.urls + patients_router.urls + doctors_router.urls + [
    path('payment/', views.PaymentProcessSandboxGenericAPIView.as_view(), name='payment-process-sandbox'),
    path('payment/callback/', views.PaymentCallbackSandboxAPIView.as_view(), name='payment-callback-sandbox'),
    path('request-doctor/', views.RequestDoctorGenericAPIView.as_view(), name='request-doctor')
]
