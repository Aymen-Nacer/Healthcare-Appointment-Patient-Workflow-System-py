import bcrypt
from django.core.management.base import BaseCommand
from healthcare.models import User, DoctorProfile, PatientProfile, UserRole


class Command(BaseCommand):
    help = 'Seed the database with demo users'

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write(self.style.WARNING('Database already seeded. Skipping.'))
            return

        def hash_pw(pw):
            return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        admin = User.objects.create(
            name='Admin User',
            email='admin@healthcare.com',
            password_hash=hash_pw('Admin@123'),
            role=UserRole.ADMIN,
        )

        doctor1 = User.objects.create(
            name='Dr. Alice Smith',
            email='alice.smith@healthcare.com',
            password_hash=hash_pw('Doctor@123'),
            role=UserRole.DOCTOR,
        )

        doctor2 = User.objects.create(
            name='Dr. Bob Johnson',
            email='bob.johnson@healthcare.com',
            password_hash=hash_pw('Doctor@123'),
            role=UserRole.DOCTOR,
        )

        patient1 = User.objects.create(
            name='Carol White',
            email='carol.white@email.com',
            password_hash=hash_pw('Patient@123'),
            role=UserRole.PATIENT,
        )

        patient2 = User.objects.create(
            name='David Brown',
            email='david.brown@email.com',
            password_hash=hash_pw('Patient@123'),
            role=UserRole.PATIENT,
        )

        DoctorProfile.objects.create(user=doctor1, specialty='Cardiology')
        DoctorProfile.objects.create(user=doctor2, specialty='General Practice')

        PatientProfile.objects.create(user=patient1)
        PatientProfile.objects.create(user=patient2)

        self.stdout.write(self.style.SUCCESS('Database seeded successfully with demo users.'))
