from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'role') and request.user.role == 'Admin'


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'role') and request.user.role == 'Doctor'


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'role') and request.user.role == 'Patient'


class IsAdminOrDoctor(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'role') and request.user.role in ('Admin', 'Doctor')
