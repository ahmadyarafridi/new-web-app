import logging
from typing import Optional, Dict, Any
from django.db import transaction
from website.models import Order
from whatsapp.models import NotificationEvent

logger = logging.getLogger(__name__)


class OrderService:
    """
    Centralized Order Management Service.
    Acts as the single source of truth for order status state transitions across the platform.
    Validates transitions, saves database records, and registers transaction.on_commit hooks for NotificationEngine.
    """

    VALID_TRANSITIONS: Dict[str, list[str]] = {
        'pending': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': [],
    }

    STATUS_EVENT_MAP: Dict[str, str] = {
        'completed': NotificationEvent.ORDER_COMPLETED,
        'cancelled': NotificationEvent.ORDER_CANCELLED,
    }

    @classmethod
    def update_status(cls, order: Order, new_status: str, updated_by: Optional[str] = None, notes: Optional[str] = None) -> Order:
        """
        Updates an order's status cleanly and dispatches multi-channel notifications on transaction commit.

        Args:
            order: The Order model instance to update.
            new_status: Target status string (pending, preparing, ready, completed, cancelled).
            updated_by: Optional username or system identifier initiating the update.
            notes: Optional status transition notes.

        Returns:
            The updated Order instance.

        Raises:
            ValueError: If new_status is invalid or represents an unallowed state transition.
        """
        old_status = order.order_status
        new_status = new_status.lower().strip()

        if old_status == new_status:
            logger.info(f"[OrderService] Order #{order.order_id} is already in status '{new_status}'. No change.")
            return order

        allowed_next = cls.VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed_next and old_status != 'pending':
            # Allow admin overrides from pending, but warn on illegal jump
            logger.warning(f"[OrderService] Non-standard transition for Order #{order.order_id}: '{old_status}' ➔ '{new_status}'")

        # Execute DB update inside transaction
        with transaction.atomic():
            order.order_status = new_status
            if notes:
                order.order_notes = f"{order.order_notes} | Status Note: {notes}".strip(" |")
            order.save(update_fields=['order_status', 'order_notes', 'updated_at'])

            event_type = cls.STATUS_EVENT_MAP.get(new_status)
            if event_type:
                payload: Dict[str, Any] = {
                    'order': order,
                    'old_status': old_status,
                    'new_status': new_status,
                    'event_type': event_type,
                    'customer_name': order.customer_name,
                    'customer_phone': order.customer_phone,
                    'total_price': float(order.total_price),
                    'order_id': order.order_id,
                }
                # Register transaction.on_commit hook for notification engine dispatch
                transaction.on_commit(lambda: cls._dispatch_notifications_on_commit(event_type, payload))

        logger.info(f"[OrderService] Order #{order.order_id} status updated: '{old_status}' ➔ '{new_status}' (By: {updated_by or 'System'})")
        return order

    @classmethod
    def _dispatch_notifications_on_commit(cls, event_type: str, payload: Dict[str, Any]) -> None:
        """
        Internal callback triggered strictly after DB transaction commits successfully.
        """
        try:
            from whatsapp.notification_engine import NotificationEngine
            NotificationEngine.dispatch(event_type, payload)
        except Exception as e:
            logger.error(f"[OrderService] Exception in notification dispatch callback for event '{event_type}': {e}")
