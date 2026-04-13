from healthcare.models import Appointment, AppointmentStatus, MedicalRecord, DoctorProfile, PatientProfile
from .audit_service import log_audit


def _map_record(record, appointment):
    return {
        'id': record.id,
        'appointmentId': record.appointment_id,
        'patientName': appointment.patient.user.name if appointment.patient and appointment.patient.user else '',
        'doctorName': appointment.doctor.user.name if appointment.doctor and appointment.doctor.user else '',
        'diagnosis': record.diagnosis,
        'notes': record.notes,
        'createdAt': record.created_at,
    }


def create_medical_record(appointment_id, diagnosis, notes, doctor_user_id):
    try:
        appointment = Appointment.objects.select_related(
            'patient__user', 'doctor__user'
        ).get(id=appointment_id)
    except Appointment.DoesNotExist:
        raise LookupError(f"Appointment with ID {appointment_id} not found.")

    if appointment.status != AppointmentStatus.IN_PROGRESS:
        raise ValueError("Medical records can only be created when the appointment is InProgress.")

    if hasattr(appointment, 'medical_record'):
        try:
            existing = appointment.medical_record
            if existing is not None:
                raise ValueError("A medical record already exists for this appointment.")
        except MedicalRecord.DoesNotExist:
            pass

    try:
        doctor_profile = DoctorProfile.objects.get(user_id=doctor_user_id)
    except DoctorProfile.DoesNotExist:
        raise ValueError("Doctor profile not found.")

    if appointment.doctor_id != doctor_profile.id:
        raise PermissionError("You can only create medical records for your own appointments.")

    record = MedicalRecord.objects.create(
        appointment=appointment,
        diagnosis=diagnosis,
        notes=notes or '',
    )

    log_audit(
        'MedicalRecordCreated',
        doctor_user_id,
        'MedicalRecord',
        record.id,
        f"AppointmentId={appointment_id}, Diagnosis={diagnosis}",
    )

    return _map_record(record, appointment)


def get_medical_record_by_appointment(appointment_id, requesting_user_id, requesting_role):
    try:
        record = MedicalRecord.objects.select_related(
            'appointment__patient__user',
            'appointment__doctor__user',
        ).get(appointment_id=appointment_id)
    except MedicalRecord.DoesNotExist:
        raise LookupError(f"Medical record for appointment ID {appointment_id} not found.")

    appointment = record.appointment

    if requesting_role == 'Patient':
        try:
            patient_profile = PatientProfile.objects.get(user_id=requesting_user_id)
        except PatientProfile.DoesNotExist:
            raise PermissionError("Access denied to this medical record.")
        if appointment.patient_id != patient_profile.id:
            raise PermissionError("Access denied to this medical record.")
    elif requesting_role == 'Doctor':
        try:
            doctor_profile = DoctorProfile.objects.get(user_id=requesting_user_id)
        except DoctorProfile.DoesNotExist:
            raise PermissionError("Access denied to this medical record.")
        if appointment.doctor_id != doctor_profile.id:
            raise PermissionError("Access denied to this medical record.")

    return _map_record(record, appointment)
