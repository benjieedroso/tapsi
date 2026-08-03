from accounts.models import User

from .models import Notification


def notify(restaurant_id, ntype, title, body="", link="", roles=(), user=None):
    """FR-150/151: create notifications addressed to roles and/or a user.
    In-app only (5-second delivery for order events is handled by polling)."""
    target_roles = [r for r in roles if r in {User.Role.OWNER, User.Role.MANAGER, User.Role.CASHIER, User.Role.KITCHEN}]
    created = []
    if user is not None:
        created.append(Notification.objects.create(
            restaurant_id=restaurant_id, type=ntype, title=title, body=body,
            link=link, user=user,
        ))
    for role in target_roles:
        created.append(Notification.objects.create(
            restaurant_id=restaurant_id, type=ntype, title=title, body=body,
            link=link, target_role=role,
        ))
    return created


def notify_role(restaurant_id, ntype, title, role, body="", link=""):
    return notify(restaurant_id, ntype, title, body=body, link=link, roles=(role,))


class Notifier:
    """Event-driven convenience facade used by order/expense workflows
    (FR-150): each method fans out notifications to the relevant roles."""

    def order_placed(self, order):
        """FR-150: new order placed → Kitchen (via kitchen queue)."""
        return notify(
            order.restaurant_id, Notification.Type.NEW_ORDER,
            f"New order {order.order_number}",
            body=f"{order.get_order_type_display()} order of ₱{order.total:.2f} is waiting in the kitchen queue.",
            link=f"/orders/{order.pk}/", roles=(User.Role.KITCHEN,),
        )

    def order_completed(self, order):
        return notify(
            order.restaurant_id, Notification.Type.NEW_ORDER,
            f"Order {order.order_number} completed",
            body=f"Total paid: ₱{order.total:.2f}. Stock was deducted via recipes.",
            link=f"/orders/{order.pk}/", roles=(User.Role.KITCHEN,),
        )

    def order_cancelled(self, order):
        """FR-150: order cancelled → Kitchen and Manager."""
        return notify(
            order.restaurant_id, Notification.Type.ORDER_CANCELLED,
            f"Order {order.order_number} cancelled",
            body=order.cancel_reason or "Cancelled",
            link=f"/orders/{order.pk}/",
            roles=(User.Role.KITCHEN, User.Role.MANAGER),
        )

    def large_discount(self, order, user):
        """FR-150/FR-087: large discount applied → Owner/Manager."""
        return notify(
            order.restaurant_id, Notification.Type.LARGE_DISCOUNT,
            f"Large discount on {order.order_number}",
            body=f"₱{order.discount_amount:.2f} ({order.get_discount_type_display()}) applied by {user.email}; "
                 f"approval {'pending' if order.discount_needs_approval else 'granted'}.",
            link=f"/orders/{order.pk}/",
            roles=(User.Role.OWNER, User.Role.MANAGER),
        )

    def refund_issued(self, refund):
        return notify(
            refund.restaurant_id, Notification.Type.ORDER_CANCELLED,
            f"Refund of ₱{refund.amount:.2f}",
            body=f"{refund.get_method_display()} refund on {refund.order.order_number} — {refund.refund_reason}",
            link=f"/orders/{refund.order_id}/",
            roles=(User.Role.OWNER, User.Role.MANAGER),
        )

    def po_received(self, po):
        """FR-150: PO received → Manager (and Owner)."""
        return notify(
            po.restaurant_id, Notification.Type.PO_RECEIVED,
            f"{po.po_number} received",
            body=f"Stock updated for supplier {po.supplier.name}.",
            link=f"/suppliers/po/{po.pk}/",
            roles=(User.Role.OWNER, User.Role.MANAGER),
        )
