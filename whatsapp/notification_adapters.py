import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from django.utils import timezone
from website.models import Order, OrderNotification
from whatsapp.models import NotificationLog, NotificationEvent
from whatsapp.template_renderer import TemplateRenderer
from whatsapp.services import WhatsAppService

logger = logging.getLogger(__name__)


@dataclass
class AdapterResult:
    """
    Standardized result contract returned by all notification adapters.
    """
    success: bool
    channel: str
    provider: str
    provider_message_id: str = ""
    error: Optional[str] = None


class NotificationAdapter(ABC):
    """
    Abstract Base Class for multi-channel Notification Adapters.
    """

    @property
    @abstractmethod
    def channel(self) -> str:
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        pass

    @abstractmethod
    def send(self, order: Order, event_type: str, context: Dict[str, Any]) -> AdapterResult:
        pass


class WhatsAppAdapter(NotificationAdapter):
    """
    WhatsApp Delivery Adapter using Meta Cloud API v20.0 and immutable per-attempt NotificationLog auditing.
    """

    @property
    def channel(self) -> str:
        return 'whatsapp'

    @property
    def provider(self) -> str:
        return 'meta'

    def send(self, order: Order, event_type: str, context: Dict[str, Any]) -> AdapterResult:
        recipient = order.customer_phone
        if not recipient or len(recipient) < 8:
            return AdapterResult(
                success=False,
                channel=self.channel,
                provider=self.provider,
                error=f"Invalid phone number '{recipient}'"
            )

        # Render message body via TemplateRenderer
        rendered_body = TemplateRenderer.render(self.channel, event_type, context)

        # Calculate attempt number per order/channel/event
        previous_attempts = NotificationLog.objects.filter(
            order=order,
            channel=self.channel,
            event_type=event_type
        ).count()
        attempt_number = previous_attempts + 1

        # Dispatch via WhatsAppService
        api_res = WhatsAppService.send_text_message(recipient, rendered_body)

        is_success = False
        msg_id = ""
        error_msg = ""

        if isinstance(api_res, dict) and api_res.get('status') == 'mocked':
            is_success = True
            msg_id = f"mock-{order.order_id}-{attempt_number}"
        elif isinstance(api_res, dict) and 'messages' in api_res:
            is_success = True
            msg_id = api_res['messages'][0].get('id', '')
        else:
            is_success = False
            error_msg = str(api_res.get('error', api_res))

        # Log immutable attempt row in NotificationLog
        NotificationLog.objects.create(
            order=order,
            channel=self.channel,
            provider=self.provider,
            event_type=event_type,
            attempt_number=attempt_number,
            recipient=recipient,
            rendered_message=rendered_body,
            status='sent' if is_success else 'failed',
            provider_message_id=msg_id,
            error_message=error_msg,
            created_at=timezone.now()
        )

        return AdapterResult(
            success=is_success,
            channel=self.channel,
            provider=self.provider,
            provider_message_id=msg_id,
            error=error_msg if not is_success else None
        )


class DashboardBellAdapter(NotificationAdapter):
    """
    Owner Dashboard Audio Bell Alert Adapter.
    Creates OrderNotification database records for live dashboard audio chime & badge.
    """

    @property
    def channel(self) -> str:
        return 'dashboard'

    @property
    def provider(self) -> str:
        return 'dashboard'

    def send(self, order: Order, event_type: str, context: Dict[str, Any]) -> AdapterResult:
        title = f"Order #{order.order_id} - Status: {(context.get('new_status') or '').upper()}"
        rendered_body = f"Order #{order.order_id} for {order.customer_name} changed to {context.get('new_status')}."

        # Create core OrderNotification row for owner dashboard audio chime
        OrderNotification.objects.create(
            order=order,
            title=title,
            message=rendered_body,
            customer_name=order.customer_name,
            total_price=order.total_price,
            notification_type='status_change',
            is_read=False
        )

        previous_attempts = NotificationLog.objects.filter(
            order=order,
            channel=self.channel,
            event_type=event_type
        ).count()

        NotificationLog.objects.create(
            order=order,
            channel=self.channel,
            provider=self.provider,
            event_type=event_type,
            attempt_number=previous_attempts + 1,
            recipient='owner_dashboard',
            rendered_message=rendered_body,
            status='sent',
            provider_message_id=f"bell-{order.order_id}-{previous_attempts + 1}",
            created_at=timezone.now()
        )

        return AdapterResult(
            success=True,
            channel=self.channel,
            provider=self.provider,
            provider_message_id=f"bell-{order.order_id}"
        )
