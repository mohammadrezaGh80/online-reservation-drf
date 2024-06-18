from rest_framework.routers import DefaultRouter

from . import views


app_name = 'online_reservation'


router = DefaultRouter()
router.register('provinces', views.ProvinceViewSet, basename='province')

urlpatterns = router.urls
