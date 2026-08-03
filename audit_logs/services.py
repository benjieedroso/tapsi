from .models import AuditLog


def log(actor=None, action="", entity="", entity_id=None, before=None,
        after=None, restaurant_id=None, request=None):
    """Write an audit entry (FR-160/161). actor and request are optional;
    IP/user-agent are captured from the request when provided."""
    if restaurant_id is None and actor is not None:
        restaurant_id = actor.restaurant_id
    entry = AuditLog(
        restaurant_id=restaurant_id,
        actor=actor,
        actor_role=getattr(actor, "role", ""),
        action=action,
        entity=entity,
        entity_id=entity_id,
        before=before or {},
        after=after or {},
    )
    if request is not None:
        entry.ip_address = request.META.get("REMOTE_ADDR")
        entry.user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:500]
    entry.save()
    return entry


def log_denied(request, permission, entity="", entity_id=None):
    """FR-160: permission-denied attempts are audit-logged."""
    return log(
        actor=request.user if request.user.is_authenticated else None,
        action="PERMISSION_DENIED",
        entity=entity or permission,
        entity_id=entity_id,
        request=request,
    )
