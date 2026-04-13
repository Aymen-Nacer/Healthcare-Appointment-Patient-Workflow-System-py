import jwt
from django.conf import settings
from rest_framework import authentication, exceptions


class JWTUser:
    """Lightweight user object extracted from JWT claims."""
    def __init__(self, user_id, email, name, role):
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.name = name
        self.role = role
        self.is_authenticated = True


class CustomJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ', 1)[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_KEY,
                algorithms=['HS256'],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
            )
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')

        user_id = payload.get('userId')
        email = payload.get('email', '')
        name = payload.get('name', '')
        role = payload.get('role', '')

        if user_id is None:
            raise exceptions.AuthenticationFailed('Invalid token payload.')

        jwt_user = JWTUser(user_id=user_id, email=email, name=name, role=role)
        return (jwt_user, token)
