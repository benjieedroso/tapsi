from django.contrib.sessions.models import Session
from django.utils import timezone

from .models import AuthenticationAudit


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
