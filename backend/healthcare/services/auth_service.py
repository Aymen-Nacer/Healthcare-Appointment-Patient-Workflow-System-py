import bcrypt
from healthcare.models import User, DoctorProfile, PatientProfile, UserRole
from .token_service import generate_token


def register_user(name, email, password, role):
    if User.objects.filter(email=email).exists():
        raise ValueError("Email is already registered.")

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User.objects.create(
        name=name,
        email=email,
        password_hash=password_hash,
        role=role,
    )

    if role == UserRole.DOCTOR:
        DoctorProfile.objects.create(user=user, specialty='General')
    elif role == UserRole.PATIENT:
        PatientProfile.objects.create(user=user)

    return {
        'token': generate_token(user),
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'userId': user.id,
    }


def login_user(email, password):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise PermissionError("Invalid email or password.")

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise PermissionError("Invalid email or password.")

    return {
        'token': generate_token(user),
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'userId': user.id,
    }
