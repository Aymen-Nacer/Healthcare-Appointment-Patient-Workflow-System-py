from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register', views.auth_register),
    path('auth/login', views.auth_login),

    # Doctors
    path('doctors', views.doctors_list),

    # Appointments
    path('appointments', views.appointments_view),
    path('appointments/<int:pk>/status', views.appointments_update_status),

    # Medical Records
    path('medical-records', views.medical_records_view),
    path('medical-records/<int:appointment_id>', views.medical_records_get),

    # Audit Logs
    path('audit-logs', views.audit_logs_list),
]
