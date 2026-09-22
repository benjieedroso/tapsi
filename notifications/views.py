from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from menu.views import TenantAwareViewSet
from .serializers import NotificationSerializer


@login_required
def notification_list(request):
    """FR-152: notification center with unread count."""
    qs = Notification.for_user(request.user).select_related("user")
    return render(request, "notifications/notification_list.html", {"notifications": qs})


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = Notification.for_user(request.user).filter(pk=pk).first()
    if notification:
        notification.mark_read()
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "notifications:notification_list"
    return redirect(next_url)


@login_required
@require_POST
def notification_mark_all_read(request):
    for n in Notification.for_user(request.user).filter(read_at__isnull=True):
        n.mark_read()
    return redirect("notifications:notification_list")

#New Code
class NotificationViewSet(TenantAwareViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """FR-151: Auto-scope notifications to the current user and their assigned role."""
        return Notification.for_user(self.request.user)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Returns total unread notification count for badge counters."""
        count = Notification.unread_count(request.user)
        return Response({"unread_count": count})

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        """FR-152: Mark an individual notification as read."""
        notification = self.get_object()
        notification.mark_read()
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """FR-152: Mark all notifications for the requesting user/role as read."""
        unread_notifications = self.get_queryset().filter(read_at__isnull=True)
        updated_count = unread_notifications.update(read_at=timezone.now())
        return Response({"marked_read": updated_count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="purge-old")
    def purge_old(self, request):
        """FR-153: Purge notifications older than 90 days across the system."""
        purged_count = Notification.purge_old()
        return Response({"purged_count": purged_count}, status=status.HTTP_200_OK)
