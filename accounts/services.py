import base64
import hashlib
import hmac
import json
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import transaction
from django.utils import timezone

from .models import AuthenticationAudit, RefreshToken, User


def client_metadata(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
    return ip_address or None, request.META.get("HTTP_USER_AGENT", "")[:512]


def audit_authentication(request, action, *, user=None, email=""):
    ip_address, user_agent = client_metadata(request)
    AuthenticationAudit.objects.create(
        user=user, email=email or (user.email if user else ""), action=action,
        ip_address=ip_address, user_agent=user_agent,
    )


def invalidate_other_sessions(user, current_session_key=None):
    """Remove all server-side sessions for a user except the active one."""
    for session in Session.objects.all():
        data = session.get_decoded()
        if str(data.get("_auth_user_id")) == str(user.pk) and session.session_key != current_session_key:
            session.delete()


def is_locked(user):
    return bool(user.locked_until and user.locked_until > timezone.now())


class JWTError(ValueError):
    pass


def _b64encode(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _b64decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def encode_jwt(payload):
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode())
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signing_input = f"{encoded_header}.{encoded_payload}".encode()
    signature = hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{_b64encode(signature)}"


def decode_jwt(token, expected_type):
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}".encode()
        expected_signature = hmac.new(settings.SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, _b64decode(encoded_signature)):
            raise JWTError("Invalid signature.")
        header = json.loads(_b64decode(encoded_header))
        payload = json.loads(_b64decode(encoded_payload))
        if header != {"alg": "HS256", "typ": "JWT"} or payload.get("type") != expected_type:
            raise JWTError("Invalid token type.")
        if int(payload["exp"]) <= int(timezone.now().timestamp()):
            raise JWTError("Token has expired.")
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise JWTError("Invalid token.") from exc


def _token_payload(user, token_type, lifetime, **extra):
    now = timezone.now()
    return {
        "sub": str(user.pk), "type": token_type, "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()), **extra,
    }


def issue_token_pair(user):
    refresh_expiry = timezone.now() + settings.JWT_REFRESH_TOKEN_LIFETIME
    refresh_record = RefreshToken.objects.create(
        user=user, jti=secrets.token_urlsafe(32), expires_at=refresh_expiry,
    )
    access = encode_jwt(_token_payload(
        user, "access", settings.JWT_ACCESS_TOKEN_LIFETIME, role=user.role,
    ))
    refresh = encode_jwt(_token_payload(
        user, "refresh", settings.JWT_REFRESH_TOKEN_LIFETIME, jti=refresh_record.jti,
    ))
    return {"access": access, "refresh": refresh, "token_type": "Bearer", "expires_in": 15 * 60}


@transaction.atomic
def rotate_refresh_token(refresh):
    payload = decode_jwt(refresh, "refresh")
    record = RefreshToken.objects.select_for_update().select_related("user").filter(jti=payload.get("jti")).first()
    if not record or not record.is_active or str(record.user_id) != payload.get("sub") or not record.user.is_active:
        raise JWTError("Refresh token is revoked or invalid.")
    record.revoked_at = timezone.now()
    record.save(update_fields=["revoked_at"])
    return issue_token_pair(record.user)


def revoke_refresh_token(refresh):
    payload = decode_jwt(refresh, "refresh")
    updated = RefreshToken.objects.filter(jti=payload.get("jti"), user_id=payload.get("sub"), revoked_at__isnull=True).update(revoked_at=timezone.now())
    if not updated:
        raise JWTError("Refresh token is revoked or invalid.")


def revoke_all_refresh_tokens(user):
    RefreshToken.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())
