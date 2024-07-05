from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from django.utils.translation import gettext as _
from django.http import Http404
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from functools import cached_property

from .models import Doctor, DoctorInsurance, DoctorSpecialty, Insurance, Patient, Province, City, Reserve, Comment
from . import serializers
from .paginations import CustomLimitOffsetPagination
from .filters import PatientFilter, DoctorFilter

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
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.ProvinceDetailSerializer
        return serializers.ProvinceSerializer


class CityViewSet(ModelViewSet):
    serializer_class = serializers.CitySerializer
    pagination_class = CustomLimitOffsetPagination

    @cached_property
    def province(self):
        try:
            province_pk = int(self.kwargs.get('province_pk'))
            province = Province.objects.get(id=province_pk)
        except (ValueError, Province.DoesNotExist):
            raise Http404
        
        return province

    def get_queryset(self):     
        return City.objects.filter(province=self.province).order_by('-id')
    
    def get_serializer_context(self):
        return {'province': self.province}


class InsuranceViewSet(ModelViewSet):
    queryset = Insurance.objects.all().order_by('-id')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.InsuranceDetailSerializer
        return serializers.InsuranceSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.patients.count() > 0:
            return Response({'detail': _('There is some patients relating this insurance, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PatientViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'put']
    queryset = Patient.objects.select_related('insurance', 'user', 'province', 'city').order_by('-created_datetime')
    pagination_class = CustomLimitOffsetPagination
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PatientFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.PatientSerializer
        elif self.action == 'retrieve':
            return serializers.PatientDetailSerializer
        return serializers.PatientUpdateSerializer
    
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        user = request.user
        patient = get_object_or_404(self.queryset, user_id=user.id)

        if request.method == 'GET':
            serializer = serializers.PatientDetailSerializer(patient)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'PUT':
            serializer = serializers.PatientUpdateSerializer(patient, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


class ReservePatientViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'patch', 'delete']
    pagination_class = CustomLimitOffsetPagination

    @cached_property
    def patient(self):
        patient_pk = self.kwargs.get('patient_pk')

        if patient_pk == 'me':
            patient = Patient.objects.get(user=self.request.user)
        else:
            try:
                patient = Patient.objects.get(user_id=patient_pk)
            except (Patient.DoesNotExist, ValueError):
                raise Http404

        return patient
    
    def get_permissions(self):
        patient_pk = self.kwargs.get('patient_pk')

        if patient_pk == 'me' and self.action not in ['partial_update', 'destroy']:
            return [IsAuthenticated()]
        else:
            return [IsAdminUser()]
    
    def get_queryset(self):
        queryset = Reserve.objects.select_related('doctor').filter(patient=self.patient)
        if self.action == 'retrieve':
            return queryset.select_related('doctor__province', 'doctor__city').prefetch_related('doctor__comments').prefetch_related(
                   Prefetch('doctor__reserves',
                            queryset=Reserve.objects.filter(status=Reserve.RESERVE_STATUS_PAID),
                            to_attr='doctor_reserves')
                ).prefetch_related(
                    Prefetch('doctor__specialties',
                             queryset=DoctorSpecialty.objects.select_related('specialty'))
                )
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return serializers.ReservePatientUpdateSerializer
        elif self.action == 'retrieve':
            return serializers.ReservePatientDetailSerializer
        return serializers.ReservePatientSerializer


class DoctorViewSet(ModelViewSet):
    queryset = Doctor.objects.filter(status=Doctor.DOCTOR_STATUS_ACCEPTED).select_related('province', 'city')\
               .prefetch_related(
                   Prefetch('reserves',
                            queryset=Reserve.objects.filter(status=Reserve.RESERVE_STATUS_PAID),
                            to_attr='doctor_reserves')
                ).prefetch_related(
                    Prefetch('specialties',
                             queryset=DoctorSpecialty.objects.select_related('specialty'))
                ).prefetch_related(
                    Prefetch('insurances',
                             queryset=DoctorInsurance.objects.select_related('insurance'))
                ).prefetch_related(
                    Prefetch('comments',
                             queryset=Comment.objects.select_related('patient').order_by('-created_datetime'))
                ).order_by('-confirm_datetime')
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = DoctorFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.DoctorDetailSerializer
        elif self.action == 'create':
            return serializers.DoctorCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.DoctorUpdateSerializer
        return serializers.DoctorSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [IsAdminUser()]
        return super().get_permissions()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.reserves.count() > 0:
            return Response({'detail': _('There is some reserves relating this doctor, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['GET', 'PUT', 'PATCH', 'DELETE'], permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        user = request.user
        doctor = get_object_or_404(self.queryset, user_id=user.id)

        if request.method == 'GET':
            serializer = serializers.DoctorDetailSerializer(doctor)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method in ['PUT', 'PATCH']:
            partial = False
            if request.method == 'PATCH':
                partial = True
            serializer = serializers.DoctorUpdateSerializer(doctor, data=request.data,  partial=partial, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            if doctor.reserves.count() > 0:
                return Response({'detail': _('There is some reserves relating to you, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
            
            doctor.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
