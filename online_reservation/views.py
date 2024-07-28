from rest_framework import status as status_code
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.utils.translation import gettext as _
from django.http import Http404
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.urls import reverse

from django_filters.rest_framework import DjangoFilterBackend
from functools import cached_property
from datetime import datetime, timedelta, timezone

from .models import Doctor, DoctorInsurance, DoctorSpecialty, Insurance, Patient, Province, City, Reserve, Comment, Specialty
from . import serializers
from .paginations import CustomLimitOffsetPagination
from .filters import PatientFilter, DoctorFilter, CommentListWaitingFilter, ReserveDoctorFilter
from .permissions import IsDoctor, IsPatientInfoComplete, IsDoctorOfficeAddressInfoComplete, IsDoctorOfficeAddressInfoCompleteForAdmin, IsDoctorOrPatient
from .payment import ZarinpalSandbox


TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))


class ProvinceViewSet(ModelViewSet):
    queryset = Province.objects.order_by('-id')
    serializer_class = serializers.ProvinceSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.doctors.count() > 0:
            return Response({'detail': _('There is some doctors relating this province, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
        elif instance.patients.count() > 0:
            return Response({'detail': _('There is some patients relating this province, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)
    
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
            return Response({'detail': _('There is some patients relating this insurance, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)


class SpecialtyViewSet(ModelViewSet):
    queryset = Specialty.objects.all().order_by('-id')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.SpecialtyDetailSerializer
        return serializers.SpecialtySerializer


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
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        elif request.method == 'PUT':
            serializer = serializers.PatientUpdateSerializer(patient, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status_code.HTTP_200_OK)


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
                patient = Patient.objects.get(id=patient_pk)
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
        queryset = Reserve.objects.select_related('doctor').filter(patient=self.patient).order_by('-reserve_datetime')
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
                             queryset=Comment.objects.filter(status=Comment.COMMENT_STATUS_APPROVED).select_related('patient').order_by('-created_datetime'))
                ).prefetch_related(
                    Prefetch('reserves',
                             queryset=Reserve.objects.filter(reserve_datetime__gte=datetime.now(tz=TEHRAN_TZ), patient__isnull=True).order_by('reserve_datetime'),
                             to_attr='doctor_free_reserves')
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
            return Response({'detail': _('There is some reserves relating this doctor, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response(status=status_code.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['GET', 'PUT', 'PATCH', 'DELETE'], permission_classes=[IsDoctor])
    def me(self, request, *args, **kwargs):
        user = request.user
        doctor = self.queryset.get(user_id=user.id)

        if request.method == 'GET':
            serializer = serializers.DoctorDetailSerializer(doctor)
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        elif request.method in ['PUT', 'PATCH']:
            partial = False
            if request.method == 'PATCH':
                partial = True
            serializer = serializers.DoctorUpdateSerializer(doctor, data=request.data,  partial=partial, context=self.get_serializer_context())
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status_code.HTTP_200_OK)
        elif request.method == 'DELETE':
            if doctor.reserves.count() > 0:
                return Response({'detail': _('There is some reserves relating to you, Please remove them first.')}, status=status_code.HTTP_400_BAD_REQUEST)
            
            doctor.delete()
            return Response(status=status_code.HTTP_204_NO_CONTENT)


class CommentViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'delete']

    def get_permissions(self):
        doctor_pk = self.kwargs.get('doctor_pk')

        if doctor_pk == 'me':
            if self.action == 'create':
                raise PermissionDenied(detail=_('You do not have permission to create a comment for yourself.'))
            return [IsDoctor()]
        
        if self.action == 'create':
            return [IsAuthenticated(), IsPatientInfoComplete()]
        elif self.action in ['retrieve', 'destroy']:
            return [IsAdminUser()]
        return super().get_permissions()

    @cached_property
    def doctor(self):
        doctor_pk = self.kwargs.get('doctor_pk')

        if doctor_pk == 'me':
            doctor = Doctor.objects.get(user=self.request.user)
        else:
            try:
                doctor = Doctor.objects.get(id=doctor_pk)
            except (Doctor.DoesNotExist, ValueError):
                raise Http404

        return doctor
    
    def get_queryset(self):
        if self.action == 'retrieve':
            return Comment.objects.filter(doctor=self.doctor, status=Comment.COMMENT_STATUS_APPROVED).select_related('patient__province', 'patient__city').order_by('-created_datetime')
        return Comment.objects.filter(doctor=self.doctor, status=Comment.COMMENT_STATUS_APPROVED).select_related('patient').order_by('-created_datetime')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.CommentDetailSerializer
        return serializers.CommentSerializer

    def get_serializer_context(self):
        return {'request': self.request, 'doctor': self.doctor}


class CommentListWaitingViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'patch']
    queryset = Comment.objects.filter(status=Comment.COMMENT_STATUS_WAITING).select_related('patient', 'doctor').order_by('-created_datetime')
    permission_classes = [IsAdminUser]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CommentListWaitingFilter

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return serializers.CommentChangeStatusSerializer
        elif self.action == 'retrieve':
            return serializers.CommentListWaitingDetailSerializer
        return serializers.CommentListWaitingSerializer
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        comment_status = serializer.validated_data.get('status')
        serializer.save()
        
        if comment_status == Comment.COMMENT_STATUS_NOT_APPROVED:
            instance.delete()        
        
        return Response(serializer.data, status=status_code.HTTP_200_OK)


class ReserveDoctorViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'delete']
    pagination_class = CustomLimitOffsetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ReserveDoctorFilter

    @cached_property
    def doctor(self):
        doctor_pk = self.kwargs.get('doctor_pk')

        if doctor_pk == 'me':
            doctor = Doctor.objects.get(user=self.request.user)
        else:
            try:
                doctor = Doctor.objects.get(id=doctor_pk)
            except (Doctor.DoesNotExist, ValueError):
                raise Http404

        return doctor
    
    def get_queryset(self):
        if self.action == 'retrieve':
            return Reserve.objects.filter(doctor=self.doctor).select_related('patient__province', 'patient__city', 'patient__insurance').order_by('-reserve_datetime')
        return Reserve.objects.filter(doctor=self.doctor).select_related('patient').order_by('-reserve_datetime')
    
    def get_permissions(self):
        doctor_pk = self.kwargs.get('doctor_pk')

        if doctor_pk == 'me':
            if self.action == 'create':
                return [IsDoctor(), IsDoctorOfficeAddressInfoComplete()]
            return [IsDoctor()]
        else:
            if self.action == 'create':
                return [IsAdminUser(), IsDoctorOfficeAddressInfoCompleteForAdmin()]
            return [IsAdminUser()]
        
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.ReserveDoctorDetailSerializer
        elif self.action == 'create':
            return serializers.ReserveDoctorCreateSerializer
        return serializers.ReserveDoctorSerializer
    
    def get_serializer_context(self):
        return {'doctor': self.doctor}


class PaymentProcessSandboxGenericAPIView(generics.GenericAPIView):
    serializer_class = serializers.ReservePaymentQueryParamSerializer
    permission_classes = [IsAuthenticated, IsPatientInfoComplete]

    def get_queryset(self):
        return Reserve.objects.prefetch_related(
            Prefetch('doctor__specialties',
                     queryset=DoctorSpecialty.objects.select_related('specialty'))
        ).select_related('doctor', 'patient__province', 'patient__city', 'patient__insurance')

    def get(self, request, *args, **kwargs):
        serializer_query_param = self.get_serializer(data=request.query_params)
        serializer_query_param.is_valid(raise_exception=True)

        reserve_id = serializer_query_param.validated_data.get('reserve_id')
        reserve = self.get_queryset().get(pk=reserve_id)

        if not reserve.patient:
            reserve.patient = request.user.patient
            reserve.save(update_fields=['patient'])

        serializer = serializers.ReservePaymentSerializer(reserve)
        return Response(serializer.data, status=status_code.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        serializer_query_param = self.get_serializer(data=request.data)
        serializer_query_param.is_valid(raise_exception=True)

        reserve_id = serializer_query_param.validated_data.get('reserve_id')
        reserve = self.get_queryset().get(pk=reserve_id)

        if not reserve.patient:
            reserve.patient = request.user.patient
            reserve.save(update_fields=['patient'])
        
        zarinpal_sandbox = ZarinpalSandbox(settings.ZARINPAL_MERCHANT_ID)
        data = zarinpal_sandbox.payment_request(
            toman_total_price=reserve.price, 
            description=f'#{reserve.id}: {reserve.patient.full_name}',
            callback_url=request.build_absolute_uri(reverse('online_reservation:payment-callback-sandbox'))
        )

        authority = data['Authority']
        
        reserve.zarinpal_authority = authority
        reserve.save(update_fields=['zarinpal_authority'])

        if 'errors' not in data or len(data['errors']) == 0:
            return redirect(zarinpal_sandbox.generate_payment_page_url(authority=authority))
        else:
            return Response({'detail': _('Error from zarinpal.')}, status=status_code.HTTP_400_BAD_REQUEST)


class PaymentCallbackSandboxAPIView(APIView):

    def get(self, request, *args, **kwargs):
        status = request.query_params.get('Status')
        authority = request.query_params.get('Authority')

        reserve = get_object_or_404(Reserve, zarinpal_authority=authority)

        if status == 'OK':
            zarinpal_sandbox = ZarinpalSandbox(settings.ZARINPAL_MERCHANT_ID)
            data = zarinpal_sandbox.payment_verify(
                toman_total_price=reserve.price, 
                authority=authority
            )
            
            payment_status = data['Status']

            if payment_status == 100:
                reserve.status = Reserve.RESERVE_STATUS_PAID
                reserve.zarinpal_ref_id = data['RefID']
                reserve.save(update_fields=['status', 'zarinpal_ref_id'])

                return Response({'detail': _('Your payment has been successfully complete.')}, status=status_code.HTTP_200_OK)
            elif payment_status == 101:
                return Response({'detail': _('Your payment has been successfully complete and has already been register.')}, status=status_code.HTTP_200_OK)
            else:
                return Response({'detail': _('The payment was unsuccessful.')}, status=status_code.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': _('The payment was unsuccessful.')}, status=status_code.HTTP_400_BAD_REQUEST)


class RequestDoctorGenericAPIView(generics.GenericAPIView):
    serializer_class = serializers.RequestDoctorSerializer
    permission_classes = [IsAuthenticated, IsDoctorOrPatient]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': _('Your request has been successfully registered.')}, status=status_code.HTTP_200_OK)
