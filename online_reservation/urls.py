from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from . import views


app_name = 'online_reservation'


router = DefaultRouter()
router.register('provinces', views.ProvinceViewSet, basename='province')
router.register('insurances', views.InsuranceViewSet, basename='insurance')
router.register('patients', views.PatientViewSet, basename='patient')
router.register('doctors', views.DoctorViewSet, basename='doctor')

provinces_router = routers.NestedDefaultRouter(router, 'provinces', lookup='province')
provinces_router.register('cities', views.CityViewSet, basename='province-cities')

patients_router = routers.NestedDefaultRouter(router, 'patients', lookup='patient')
patients_router.register('reserves', views.ReservePatientViewSet, basename='patient-reserves')

urlpatterns = router.urls + provinces_router.urls + patients_router.urls
