from django.contrib import admin
from .models import User, DoctorProfile, PatientProfile, Appointment, MedicalRecord, AuditLog

admin.site.register(User)
admin.site.register(DoctorProfile)
admin.site.register(PatientProfile)
admin.site.register(Appointment)
admin.site.register(MedicalRecord)
admin.site.register(AuditLog)
