from rest_framework import serializers
from .models import User, DoctorProfile, Appointment, MedicalRecord, AuditLog


# Auth
class RegisterRequestSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    role = serializers.ChoiceField(choices=['Admin', 'Doctor', 'Patient'])


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    name = serializers.CharField()
    email = serializers.CharField()
    role = serializers.CharField()
    userId = serializers.IntegerField()


# Doctors
class DoctorResponseSerializer(serializers.Serializer):
    doctorProfileId = serializers.IntegerField()
    userId = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()
    specialty = serializers.CharField()


# Appointments
class CreateAppointmentRequestSerializer(serializers.Serializer):
    doctorId = serializers.IntegerField()
    startTime = serializers.DateTimeField()
    endTime = serializers.DateTimeField()


class UpdateAppointmentStatusRequestSerializer(serializers.Serializer):
    newStatus = serializers.ChoiceField(choices=['Scheduled', 'Confirmed', 'InProgress', 'Completed', 'Cancelled'])
    rowVersion = serializers.IntegerField(required=False, allow_null=True)


class AppointmentResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    patientId = serializers.IntegerField()
    patientName = serializers.CharField()
    doctorId = serializers.IntegerField()
    doctorName = serializers.CharField()
    doctorSpecialty = serializers.CharField()
    startTime = serializers.DateTimeField()
    endTime = serializers.DateTimeField()
    status = serializers.CharField()
    rowVersion = serializers.IntegerField()


# Medical Records
class CreateMedicalRecordRequestSerializer(serializers.Serializer):
    appointmentId = serializers.IntegerField()
    diagnosis = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class MedicalRecordResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    appointmentId = serializers.IntegerField()
    patientName = serializers.CharField()
    doctorName = serializers.CharField()
    diagnosis = serializers.CharField()
    notes = serializers.CharField()
    createdAt = serializers.DateTimeField()


# Audit Logs
class AuditLogResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    action = serializers.CharField()
    entityId = serializers.IntegerField()
    performedByUserId = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    metadata = serializers.CharField(allow_null=True)
    entityName = serializers.CharField()
