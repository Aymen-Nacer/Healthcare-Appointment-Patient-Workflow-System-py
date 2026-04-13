from django.db import models


class UserRole(models.TextChoices):
    ADMIN = 'Admin', 'Admin'
    DOCTOR = 'Doctor', 'Doctor'
    PATIENT = 'Patient', 'Patient'


class AppointmentStatus(models.TextChoices):
    SCHEDULED = 'Scheduled', 'Scheduled'
    CONFIRMED = 'Confirmed', 'Confirmed'
    IN_PROGRESS = 'InProgress', 'InProgress'
    COMPLETED = 'Completed', 'Completed'
    CANCELLED = 'Cancelled', 'Cancelled'


class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=UserRole.choices)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.name} ({self.role})"


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=255)

    class Meta:
        db_table = 'doctor_profiles'

    def __str__(self):
        return f"Dr. {self.user.name} - {self.specialty}"


class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')

    class Meta:
        db_table = 'patient_profiles'

    def __str__(self):
        return f"Patient: {self.user.name}"


class Appointment(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.RESTRICT, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.RESTRICT, related_name='appointments')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.SCHEDULED)
    version = models.IntegerField(default=1)

    class Meta:
        db_table = 'appointments'

    def __str__(self):
        return f"Appointment #{self.id} - {self.status}"


class MedicalRecord(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='medical_record')
    diagnosis = models.CharField(max_length=1000)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medical_records'

    def __str__(self):
        return f"Record for Appointment #{self.appointment_id}"


class AuditLog(models.Model):
    action = models.CharField(max_length=255)
    performed_by_user_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    entity_name = models.CharField(max_length=255)
    entity_id = models.IntegerField()
    metadata = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} by User#{self.performed_by_user_id}"
