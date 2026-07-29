import logging
from typing import Dict, Any, List
from website.models import Order
from whatsapp.models import NotificationLog, NotificationEvent
from whatsapp.notification_adapters import (
    NotificationAdapter,
    WhatsAppAdapter,
    DashboardBellAdapter,
    AdapterResult
)

logger = logging.getLogger(__name__)


class NotificationEngine:
    """
    Generic Multi-Channel Notification Orchestration Engine.
    Exposes a stateless dispatch(event_type, payload) entrypoint ready for background task queues.
    Enforces per-adapter isolation (one failure does not block other channels).
    """

    _adapters: List[NotificationAdapter] = [
        WhatsAppAdapter(),
        DashboardBellAdapter(),
    ]

    @classmethod
    def register_adapter(cls, adapter: NotificationAdapter) -> None:
        """
        Dynamically registers a new channel adapter (e.g. EmailAdapter, SMSAdapter).
        """
        cls._adapters.append(adapter)
        logger.info(f"[NotificationEngine] Registered new adapter: '{adapter.channel}' ({adapter.provider})")

    @classmethod
    def dispatch(cls, event_type: str, payload: Dict[str, Any]) -> Dict[str, AdapterResult]:
        """
        Generic dispatch entrypoint.
        Orchestrates notification delivery across all registered adapters with error boundaries.

        Args:
            event_type: Value from NotificationEvent (e.g. order_preparing, order_ready).
            payload: Dict containing order instance, customer info, and status context.

        Returns:
            Dict mapping channel name -> AdapterResult.
        """
        order: Order = payload.get('order')
        if not order:
            logger.error(f"[NotificationEngine] Missing 'order' in payload for event '{event_type}'")
            return {}

        results: Dict[str, AdapterResult] = {}

        logger.info(f"[NotificationEngine] Dispatching event '{event_type}' for Order #{order.order_id} across {len(cls._adapters)} adapters.")

        for adapter in cls._adapters:
            # Per-Adapter Error Boundary
            try:
                # Idempotency check: if sent successfully on this channel/event, skip duplicate
                already_sent = NotificationLog.objects.filter(
                    order=order,
                    channel=adapter.channel,
                    event_type=event_type,
                    status='sent'
                ).exists()

                if already_sent:
                    logger.info(f"[NotificationEngine] Event '{event_type}' already sent for Order #{order.order_id} via channel '{adapter.channel}'. Skipping duplicate.")
                    results[adapter.channel] = AdapterResult(
                        success=True,
                        channel=adapter.channel,
                        provider=adapter.provider,
                        error="Duplicate suppressed by NotificationEngine"
                    )
                    continue

                res = adapter.send(order, event_type, payload)
                results[adapter.channel] = res
                logger.info(f"[NotificationEngine] Adapter '{adapter.channel}' result for Order #{order.order_id}: Success={res.success}")

            except Exception as e:
                logger.error(f"[NotificationEngine] Exception in adapter '{adapter.channel}' for Order #{order.order_id}: {e}")
                results[adapter.channel] = AdapterResult(
                    success=False,
                    channel=adapter.channel,
                    provider=adapter.provider,
                    error=str(e)
                )

        return results
