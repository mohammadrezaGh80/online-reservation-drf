from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from django.utils.translation import gettext as _

from .models import Province
from . import serializers
from .paginations import CustomLimitOffsetPagination


class ProvinceViewSet(ModelViewSet):
    queryset = Province.objects.order_by('-id')
    serializer_class = serializers.ProvinceSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.doctors.count() > 0:
            return Response({'detail': _('There is some doctors relating this province, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
        elif instance.patients.count() > 0:
            return Response({'detail': _('There is some patients relating this province, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
