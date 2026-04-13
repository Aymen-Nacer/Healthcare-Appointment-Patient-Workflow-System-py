from datetime import datetime, timezone
from django.db import transaction
from healthcare.models import (
    Appointment, AppointmentStatus, PatientProfile, DoctorProfile,
)
from .audit_service import log_audit


def _map_appointment(a):
    return {
        'id': a.id,
        'patientId': a.patient_id,
        'patientName': a.patient.user.name,
        'doctorId': a.doctor_id,
        'doctorName': a.doctor.user.name,
        'doctorSpecialty': a.doctor.specialty,
        'startTime': a.start_time,
        'endTime': a.end_time,
        'status': a.status,
        'rowVersion': a.version,
    }


def create_appointment(doctor_id, start_time, end_time, patient_user_id):
    if start_time <= datetime.now(timezone.utc):
        raise ValueError("Cannot book an appointment in the past.")

    if end_time <= start_time:
        raise ValueError("EndTime must be after StartTime.")

    try:
        patient_profile = PatientProfile.objects.select_related('user').get(user_id=patient_user_id)
    except PatientProfile.DoesNotExist:
        raise ValueError("Patient profile not found for the current user.")

    try:
        doctor_profile = DoctorProfile.objects.select_related('user').get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        raise LookupError(f"Doctor with ID {doctor_id} not found.")

    with transaction.atomic():
        has_overlap = Appointment.objects.filter(
            doctor_id=doctor_id,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(status=AppointmentStatus.CANCELLED).exists()

        if has_overlap:
            raise ValueError("The doctor already has an appointment during this time slot.")

        appointment = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.SCHEDULED,
        )

    log_audit(
        'AppointmentCreated',
        patient_user_id,
        'Appointment',
        appointment.id,
        f"PatientId={patient_profile.id}, DoctorId={doctor_id}, StartTime={start_time.isoformat()}",
    )

    return _map_appointment(appointment)


def get_appointments(doctor_id_filter, patient_id_filter, requesting_user_id, requesting_role):
    qs = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).order_by('-start_time')

    if requesting_role == 'Patient':
        try:
            patient_profile = PatientProfile.objects.get(user_id=requesting_user_id)
            qs = qs.filter(patient=patient_profile)
        except PatientProfile.DoesNotExist:
            return []
    elif requesting_role == 'Doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_id=requesting_user_id)
            qs = qs.filter(doctor=doctor_profile)
        except DoctorProfile.DoesNotExist:
            return []
    else:
        if doctor_id_filter is not None:
            qs = qs.filter(doctor_id=doctor_id_filter)
        if patient_id_filter is not None:
            qs = qs.filter(patient_id=patient_id_filter)

    return [_map_appointment(a) for a in qs]


def _validate_transition(current, new_status, role):
    allowed = {
        ('Scheduled', 'Confirmed', 'Admin'),
        ('Scheduled', 'Cancelled', 'Admin'),
        ('Confirmed', 'Cancelled', 'Admin'),
        ('Confirmed', 'InProgress', 'Doctor'),
        ('InProgress', 'Completed', 'Doctor'),
    }
    if (current, new_status, role) not in allowed:
        raise ValueError(
            f"Transition from '{current}' to '{new_status}' is not allowed for role '{role}'."
        )


def update_appointment_status(appointment_id, new_status, row_version, performing_user_id, performing_role):
    try:
        appointment = Appointment.objects.select_related(
            'patient__user', 'doctor__user'
        ).get(id=appointment_id)
    except Appointment.DoesNotExist:
        raise LookupError(f"Appointment with ID {appointment_id} not found.")

    if appointment.status == AppointmentStatus.COMPLETED:
        raise ValueError("Cannot modify a completed appointment.")

    _validate_transition(appointment.status, new_status, performing_role)

    if new_status == 'Completed':
        from healthcare.models import MedicalRecord
        if not MedicalRecord.objects.filter(appointment_id=appointment_id).exists():
            raise ValueError("Cannot complete appointment without a medical record.")

    if performing_role == 'Doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_id=performing_user_id)
        except DoctorProfile.DoesNotExist:
            raise PermissionError("Doctor profile not found.")
        if doctor_profile.id != appointment.doctor_id:
            raise PermissionError("You can only update appointments assigned to you.")

    previous_status = appointment.status

    if row_version is not None:
        updated = Appointment.objects.filter(id=appointment_id, version=row_version).update(
            status=new_status,
            version=appointment.version + 1,
        )
        if updated == 0:
            raise ValueError("The appointment was modified by another user. Please refresh and try again.")
        appointment.refresh_from_db()
    else:
        appointment.status = new_status
        appointment.version += 1
        appointment.save()

    log_audit(
        'AppointmentStatusChanged',
        performing_user_id,
        'Appointment',
        appointment.id,
        f"From={previous_status}, To={new_status}",
    )

    appointment = Appointment.objects.select_related(
        'patient__user', 'doctor__user'
    ).get(id=appointment_id)

    return _map_appointment(appointment)
