from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render

from accounts.models import User

from .models import AuditLog


def _can_view(user):
    return user.is_authenticated and user.role in {User.Role.OWNER, User.Role.MANAGER}


@user_passes_test(_can_view)
def audit_log_list(request):
    """FR-163: Owners full, Managers read-only — both scoped to restaurant."""
    rid = request.user.restaurant_id
    qs = AuditLog.objects.filter(restaurant_id=rid).select_related("actor")

    action = request.GET.get("action", "")
    entity = request.GET.get("entity", "")
    actor_id = request.GET.get("actor", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    if action:
        qs = qs.filter(action=action)
    if entity:
        qs = qs.filter(entity=entity)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "audit_logs/audit_log_list.html", {
        "logs": page,
        "action": action,
        "entity": entity,
        "actor_id": actor_id,
        "date_from": date_from,
        "date_to": date_to,
        "actions": AuditLog.objects.filter(restaurant_id=rid)
            .order_by("action").values_list("action", flat=True).distinct(),
        "entities": AuditLog.objects.filter(restaurant_id=rid)
            .order_by("entity").values_list("entity", flat=True).distinct(),
        "staff": User.objects.filter(restaurant=rid).order_by("email"),
    })
