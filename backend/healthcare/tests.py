from datetime import datetime, timedelta, timezone
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from healthcare.models import (
    User, UserRole, DoctorProfile, PatientProfile,
    Appointment, AppointmentStatus, MedicalRecord, AuditLog,
)
from healthcare.services.token_service import generate_token


def _make_user(name, email, role, password='password123'):
    import bcrypt
    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User.objects.create(name=name, email=email, password_hash=pw, role=role)
    if role == UserRole.DOCTOR:
        DoctorProfile.objects.create(user=user, specialty='General')
    elif role == UserRole.PATIENT:
        PatientProfile.objects.create(user=user)
    return user


def _auth_client(user):
    client = APIClient()
    token = generate_token(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


# ---------- Model tests ----------

class ModelStrTests(TestCase):
    def test_user_str(self):
        u = User(name='Alice', role='Patient')
        self.assertIn('Alice', str(u))

    def test_appointment_str(self):
        a = Appointment(id=1, status='Scheduled')
        self.assertIn('Scheduled', str(a))

    def test_audit_log_str(self):
        log = AuditLog(action='Created', performed_by_user_id=1)
        self.assertIn('Created', str(log))


# ---------- Auth endpoint tests ----------

class AuthTests(TestCase):
    def test_register_success(self):
        client = APIClient()
        resp = client.post('/api/auth/register', {
            'name': 'Test', 'email': 'test@test.com',
            'password': 'secret123', 'role': 'Patient',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertIn('token', resp.data)
        self.assertEqual(resp.data['role'], 'Patient')

    def test_register_duplicate_email(self):
        client = APIClient()
        payload = {'name': 'A', 'email': 'dup@test.com', 'password': 'secret123', 'role': 'Patient'}
        client.post('/api/auth/register', payload, format='json')
        resp = client.post('/api/auth/register', payload, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_login_success(self):
        client = APIClient()
        client.post('/api/auth/register', {
            'name': 'A', 'email': 'log@test.com',
            'password': 'secret123', 'role': 'Patient',
        }, format='json')
        resp = client.post('/api/auth/login', {
            'email': 'log@test.com', 'password': 'secret123',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.data)

    def test_login_wrong_password(self):
        client = APIClient()
        client.post('/api/auth/register', {
            'name': 'A', 'email': 'bad@test.com',
            'password': 'secret123', 'role': 'Patient',
        }, format='json')
        resp = client.post('/api/auth/login', {
            'email': 'bad@test.com', 'password': 'wrong',
        }, format='json')
        self.assertEqual(resp.status_code, 401)

    def test_register_creates_doctor_profile(self):
        client = APIClient()
        resp = client.post('/api/auth/register', {
            'name': 'DrX', 'email': 'drx@test.com',
            'password': 'secret123', 'role': 'Doctor',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        user = User.objects.get(email='drx@test.com')
        self.assertTrue(DoctorProfile.objects.filter(user=user).exists())


# ---------- Doctors list ----------

class DoctorsListTests(TestCase):
    def test_list_doctors_authenticated(self):
        doc = _make_user('Dr.A', 'dra@test.com', UserRole.DOCTOR)
        client = _auth_client(doc)
        resp = client.get('/api/doctors')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_list_doctors_unauthenticated(self):
        resp = APIClient().get('/api/doctors')
        self.assertIn(resp.status_code, [401, 403])


# ---------- Appointment tests ----------

class AppointmentTests(TestCase):
    def setUp(self):
        self.doctor_user = _make_user('Dr.B', 'drb@test.com', UserRole.DOCTOR)
        self.patient_user = _make_user('Pat', 'pat@test.com', UserRole.PATIENT)
        self.admin_user = _make_user('Adm', 'adm@test.com', UserRole.ADMIN)
        self.doctor_profile = DoctorProfile.objects.get(user=self.doctor_user)
        self.patient_profile = PatientProfile.objects.get(user=self.patient_user)

    def _future(self, hours=1):
        start = datetime.now(timezone.utc) + timedelta(hours=hours)
        return start, start + timedelta(hours=1)

    def test_patient_creates_appointment(self):
        client = _auth_client(self.patient_user)
        start, end = self._future()
        resp = client.post('/api/appointments', {
            'doctorId': self.doctor_profile.id,
            'startTime': start.isoformat(),
            'endTime': end.isoformat(),
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['status'], 'Scheduled')

    def test_doctor_cannot_create_appointment(self):
        client = _auth_client(self.doctor_user)
        start, end = self._future()
        resp = client.post('/api/appointments', {
            'doctorId': self.doctor_profile.id,
            'startTime': start.isoformat(),
            'endTime': end.isoformat(),
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_overlap_rejected(self):
        client = _auth_client(self.patient_user)
        start, end = self._future(hours=5)
        client.post('/api/appointments', {
            'doctorId': self.doctor_profile.id,
            'startTime': start.isoformat(),
            'endTime': end.isoformat(),
        }, format='json')
        resp = client.post('/api/appointments', {
            'doctorId': self.doctor_profile.id,
            'startTime': start.isoformat(),
            'endTime': end.isoformat(),
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_patient_sees_own_appointments(self):
        client = _auth_client(self.patient_user)
        start, end = self._future(hours=10)
        client.post('/api/appointments', {
            'doctorId': self.doctor_profile.id,
            'startTime': start.isoformat(),
            'endTime': end.isoformat(),
        }, format='json')
        resp = client.get('/api/appointments')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_admin_confirms_appointment(self):
        start, end = self._future(hours=20)
        appt = Appointment.objects.create(
            patient=self.patient_profile, doctor=self.doctor_profile,
            start_time=start, end_time=end, status=AppointmentStatus.SCHEDULED,
        )
        client = _auth_client(self.admin_user)
        resp = client.patch(f'/api/appointments/{appt.id}/status', {
            'newStatus': 'Confirmed',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'Confirmed')

    def test_invalid_transition_rejected(self):
        start, end = self._future(hours=30)
        appt = Appointment.objects.create(
            patient=self.patient_profile, doctor=self.doctor_profile,
            start_time=start, end_time=end, status=AppointmentStatus.SCHEDULED,
        )
        client = _auth_client(self.admin_user)
        resp = client.patch(f'/api/appointments/{appt.id}/status', {
            'newStatus': 'Completed',
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_optimistic_concurrency(self):
        start, end = self._future(hours=40)
        appt = Appointment.objects.create(
            patient=self.patient_profile, doctor=self.doctor_profile,
            start_time=start, end_time=end, status=AppointmentStatus.SCHEDULED,
        )
        client = _auth_client(self.admin_user)
        resp = client.patch(f'/api/appointments/{appt.id}/status', {
            'newStatus': 'Confirmed', 'rowVersion': 999,
        }, format='json')
        self.assertEqual(resp.status_code, 409)


# ---------- Medical record tests ----------

class MedicalRecordTests(TestCase):
    def setUp(self):
        self.doctor_user = _make_user('Dr.C', 'drc@test.com', UserRole.DOCTOR)
        self.patient_user = _make_user('Pat2', 'pat2@test.com', UserRole.PATIENT)
        self.doctor_profile = DoctorProfile.objects.get(user=self.doctor_user)
        self.patient_profile = PatientProfile.objects.get(user=self.patient_user)
        start = datetime.now(timezone.utc) + timedelta(hours=1)
        self.appt = Appointment.objects.create(
            patient=self.patient_profile, doctor=self.doctor_profile,
            start_time=start, end_time=start + timedelta(hours=1),
            status=AppointmentStatus.IN_PROGRESS,
        )

    def test_doctor_creates_record(self):
        client = _auth_client(self.doctor_user)
        resp = client.post('/api/medical-records', {
            'appointmentId': self.appt.id,
            'diagnosis': 'Flu',
            'notes': 'Rest',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['diagnosis'], 'Flu')

    def test_patient_cannot_create_record(self):
        client = _auth_client(self.patient_user)
        resp = client.post('/api/medical-records', {
            'appointmentId': self.appt.id,
            'diagnosis': 'Flu',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_wrong_doctor_cannot_create_record(self):
        other_doc = _make_user('Dr.D', 'drd@test.com', UserRole.DOCTOR)
        client = _auth_client(other_doc)
        resp = client.post('/api/medical-records', {
            'appointmentId': self.appt.id,
            'diagnosis': 'Flu',
        }, format='json')
        self.assertEqual(resp.status_code, 403)

    def test_get_record(self):
        MedicalRecord.objects.create(
            appointment=self.appt, diagnosis='Cold', notes='',
        )
        client = _auth_client(self.doctor_user)
        resp = client.get(f'/api/medical-records/{self.appt.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['diagnosis'], 'Cold')

    def test_not_in_progress_rejected(self):
        self.appt.status = AppointmentStatus.SCHEDULED
        self.appt.save()
        client = _auth_client(self.doctor_user)
        resp = client.post('/api/medical-records', {
            'appointmentId': self.appt.id,
            'diagnosis': 'Flu',
        }, format='json')
        self.assertIn(resp.status_code, [400, 409])


# ---------- Audit log tests ----------

class AuditLogTests(TestCase):
    def test_admin_can_view_logs(self):
        admin = _make_user('Adm2', 'adm2@test.com', UserRole.ADMIN)
        AuditLog.objects.create(
            action='Test', performed_by_user_id=admin.id,
            entity_name='Test', entity_id=1,
        )
        client = _auth_client(admin)
        resp = client.get('/api/audit-logs')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_patient_cannot_view_logs(self):
        patient = _make_user('Pat3', 'pat3@test.com', UserRole.PATIENT)
        client = _auth_client(patient)
        resp = client.get('/api/audit-logs')
        self.assertEqual(resp.status_code, 403)

    def test_filter_by_action(self):
        admin = _make_user('Adm3', 'adm3@test.com', UserRole.ADMIN)
        AuditLog.objects.create(
            action='AppointmentCreated', performed_by_user_id=1,
            entity_name='Appointment', entity_id=1,
        )
        AuditLog.objects.create(
            action='MedicalRecordCreated', performed_by_user_id=1,
            entity_name='MedicalRecord', entity_id=2,
        )
        client = _auth_client(admin)
        resp = client.get('/api/audit-logs?action=Appointment')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)


# ---------- Complete workflow test ----------

class FullWorkflowTest(TestCase):
    """Register → book → confirm → start → record → complete."""

    def test_full_flow(self):
        c = APIClient()

        # Register doctor & patient
        resp = c.post('/api/auth/register', {
            'name': 'Dr.Flow', 'email': 'drflow@test.com',
            'password': 'secret123', 'role': 'Doctor',
        }, format='json')
        doc_token = resp.data['token']
        doc_id = resp.data['userId']

        resp = c.post('/api/auth/register', {
            'name': 'PatFlow', 'email': 'patflow@test.com',
            'password': 'secret123', 'role': 'Patient',
        }, format='json')
        pat_token = resp.data['token']

        resp = c.post('/api/auth/register', {
            'name': 'AdmFlow', 'email': 'admflow@test.com',
            'password': 'secret123', 'role': 'Admin',
        }, format='json')
        adm_token = resp.data['token']

        doctor_profile = DoctorProfile.objects.get(user_id=doc_id)
        start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Patient books
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {pat_token}')
        resp = c.post('/api/appointments', {
            'doctorId': doctor_profile.id,
            'startTime': start.isoformat(),
            'endTime': (start + timedelta(hours=1)).isoformat(),
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        appt_id = resp.data['id']
        version = resp.data['rowVersion']

        # Admin confirms
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {adm_token}')
        resp = c.patch(f'/api/appointments/{appt_id}/status', {
            'newStatus': 'Confirmed', 'rowVersion': version,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        version = resp.data['rowVersion']

        # Doctor starts
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {doc_token}')
        resp = c.patch(f'/api/appointments/{appt_id}/status', {
            'newStatus': 'InProgress', 'rowVersion': version,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        version = resp.data['rowVersion']

        # Doctor creates medical record
        resp = c.post('/api/medical-records', {
            'appointmentId': appt_id,
            'diagnosis': 'Healthy',
            'notes': 'All good',
        }, format='json')
        self.assertEqual(resp.status_code, 201)

        # Doctor completes
        resp = c.patch(f'/api/appointments/{appt_id}/status', {
            'newStatus': 'Completed', 'rowVersion': version,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'Completed')
