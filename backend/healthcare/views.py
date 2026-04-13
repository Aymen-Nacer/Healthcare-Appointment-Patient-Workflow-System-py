from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .authentication import CustomJWTAuthentication
from .permissions import IsAdmin, IsDoctor, IsPatient, IsAdminOrDoctor
from .serializers import (
    RegisterRequestSerializer, LoginRequestSerializer, AuthResponseSerializer,
    DoctorResponseSerializer,
    CreateAppointmentRequestSerializer, UpdateAppointmentStatusRequestSerializer,
    AppointmentResponseSerializer,
    CreateMedicalRecordRequestSerializer, MedicalRecordResponseSerializer,
    AuditLogResponseSerializer,
)
from .services.auth_service import register_user, login_user
from .services.appointment_service import create_appointment, get_appointments, update_appointment_status
from .services.medical_record_service import create_medical_record, get_medical_record_by_appointment
from .models import DoctorProfile, AuditLog


# ---------- Auth ----------

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def auth_register(request):
    serializer = RegisterRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    try:
        result = register_user(d['name'], d['email'], d['password'], d['role'])
        return Response(AuthResponseSerializer(result).data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def auth_login(request):
    serializer = LoginRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    try:
        result = login_user(d['email'], d['password'])
        return Response(AuthResponseSerializer(result).data, status=status.HTTP_200_OK)
    except PermissionError as e:
        return Response({'message': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


# ---------- Doctors ----------

@api_view(['GET'])
@authentication_classes([CustomJWTAuthentication])
@permission_classes([IsAuthenticated])
def doctors_list(request):
    doctors = DoctorProfile.objects.select_related('user').all()
    data = [
        {
            'doctorProfileId': d.id,
            'userId': d.user_id,
            'name': d.user.name,
            'email': d.user.email,
            'specialty': d.specialty,
        }
        for d in doctors
    ]
    return Response(DoctorResponseSerializer(data, many=True).data)


# ---------- Appointments ----------

@api_view(['GET', 'POST'])
@authentication_classes([CustomJWTAuthentication])
@permission_classes([IsAuthenticated])
def appointments_view(request):
    if request.method == 'POST':
        if request.user.role != 'Patient':
            return Response({'message': 'Only patients can create appointments.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CreateAppointmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            result = create_appointment(
                doctor_id=d['doctorId'],
                start_time=d['startTime'],
                end_time=d['endTime'],
                patient_user_id=request.user.id,
            )
            return Response(AppointmentResponseSerializer(result).data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except LookupError as e:
            return Response({'message': str(e)}, status=status.HTTP_404_NOT_FOUND)

    # GET
    doctor_id = request.query_params.get('doctorId')
    patient_id = request.query_params.get('patientId')
    doctor_id = int(doctor_id) if doctor_id else None
    patient_id = int(patient_id) if patient_id else None
    result = get_appointments(doctor_id, patient_id, request.user.id, request.user.role)
    return Response(AppointmentResponseSerializer(result, many=True).data)


@api_view(['PATCH'])
@authentication_classes([CustomJWTAuthentication])
@permission_classes([IsAdminOrDoctor])
def appointments_update_status(request, pk):
    serializer = UpdateAppointmentStatusRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    try:
        result = update_appointment_status(
            appointment_id=pk,
            new_status=d['newStatus'],
            row_version=d.get('rowVersion'),
            performing_user_id=request.user.id,
            performing_role=request.user.role,
        )
        return Response(AppointmentResponseSerializer(result).data)
    except LookupError as e:
        return Response({'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        msg = str(e)
        if 'modified by another user' in msg:
            return Response({'message': msg}, status=status.HTTP_409_CONFLICT)
        return Response({'message': msg}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError as e:
        return Response({'message': str(e)}, status=status.HTTP_403_FORBIDDEN)


# ---------- Medical Records ----------

@api_view(['POST'])
@authentication_classes([CustomJWTAuthentication])
@permission_classes([IsAuthenticated])
def medical_records_view(request):
    if request.user.role != 'Doctor':
        return Response({'message': 'Only doctors can create medical records.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = CreateMedicalRecordRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    d = serializer.validated_data
    try:
        result = create_medical_record(
            appointment_id=d['appointmentId'],
            diagnosis=d['diagnosis'],
            notes=d.get('notes', ''),
            doctor_user_id=request.user.id,
        )
        return Response(MedicalRecordResponseSerializer(result).data, status=status.HTTP_201_CREATED)
    except LookupError as e:
        return Response({'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        return Response({'message': str(e)}, status=status.HTTP_409_CONFLICT)
    except PermissionError as e:
        return Response({'message': str(e)}, status=status.HTTP_403_FORBIDDEN)


@api_view(['GET'])
@authentication_classes([CustomJWTAuthentication])
@permission_classes([IsAuthenticated])
def medical_records_get(request, appointment_id):
    try:
        result = get_medical_record_by_appointment(
            appointment_id=appointment_id,
            requesting_user_id=request.user.id,
            requesting_role=request.user.role,
        )
        return Response(MedicalRecordResponseSerializer(result).data)
    except LookupError as e:
        return Response({'message': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except PermissionError as e:
        return Response({'message': str(e)}, status=status.HTTP_403_FORBIDDEN)


# ---------- Audit Logs ----------

@api_view(['GET'])
@authentication_classes([CustomJWTAuthentication])
@permission_classes([IsAdmin])
def audit_logs_list(request):
    qs = AuditLog.objects.all()

    entity_id = request.query_params.get('entityId')
    action = request.query_params.get('action')
    date = request.query_params.get('date')

    if entity_id:
        qs = qs.filter(entity_id=int(entity_id))
    if action:
        qs = qs.filter(action__icontains=action)
    if date:
        qs = qs.filter(timestamp__date=date)

    qs = qs.order_by('-timestamp')

    data = [
        {
            'id': log.id,
            'action': log.action,
            'entityId': log.entity_id,
            'performedByUserId': log.performed_by_user_id,
            'timestamp': log.timestamp,
            'metadata': log.metadata,
            'entityName': log.entity_name,
        }
        for log in qs
    ]
    return Response(AuditLogResponseSerializer(data, many=True).data)
