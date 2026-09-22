from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render

from rest_framework import mixins, viewsets
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import IsAuthenticated

from menu.views import TenantAwareViewSet

from accounts.models import User
from .models import AuditLog
from .serializers import AuditLogSerializer

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

#New Code
class AuditLogViewSet(TenantAwareViewSet):
    """
    FR-160..FR-163: Read-only API for audit log trail.
    Append-only log storage prevents modification or deletion via API.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """FR-163: Scope audit records to the authenticated user's restaurant."""
        rid = self.get_restaurant_id()
        queryset = AuditLog.scoped(restaurant_id=rid).select_related("actor")

        action_param = self.request.query_params.get("action")
        entity_param = self.request.query_params.get("entity")
        entity_id_param = self.request.query_params.get("entity_id")
        actor_param = self.request.query_params.get("actor")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if action_param:
            queryset = queryset.filter(action__iexact=action_param)
        if entity_param:
            queryset = queryset.filter(entity__iexact=entity_param)
        if entity_id_param:
            queryset = queryset.filter(entity_id=entity_id_param)
        if actor_param:
            queryset = queryset.filter(actor_id=actor_param)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="FR-161: Audit logs are append-only and cannot be created via API.")

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PUT", detail="FR-162: Audit logs are append-only and cannot be modified.")

    def partial_update(self, request, *args, **kwargs):
        raise MethodNotAllowed("PATCH", detail="FR-162: Audit logs are append-only and cannot be modified.")

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE", detail="FR-163: Audit logs are append-only and cannot be deleted.")