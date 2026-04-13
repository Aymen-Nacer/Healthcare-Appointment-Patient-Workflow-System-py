import jwt
import uuid
from datetime import datetime, timezone, timedelta
from django.conf import settings


def generate_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'userId': user.id,
        'jti': str(uuid.uuid4()),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
        'iat': now,
        'exp': now + timedelta(minutes=settings.JWT_EXPIRES_IN_MINUTES),
    }
    token = jwt.encode(payload, settings.JWT_KEY, algorithm='HS256')
    return token
