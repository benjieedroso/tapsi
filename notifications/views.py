from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


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
