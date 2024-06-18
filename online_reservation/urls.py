from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from . import views


app_name = 'online_reservation'


router = DefaultRouter()
router.register('provinces', views.ProvinceViewSet, basename='province')

provinces_router = routers.NestedDefaultRouter(router, 'provinces', lookup='province')
provinces_router.register('cities', views.CityViewSet, basename='province-cities')

urlpatterns = router.urls + provinces_router.urls
