import re
import logging
from typing import Dict, Any, Set
from whatsapp.models import NotificationTemplate, NotificationEvent, WhatsAppSetting

logger = logging.getLogger(__name__)


class TemplateRenderError(Exception):
    """Raised when placeholder validation or rendering fails."""
    pass


class TemplateRenderer:
    """
    Independent Template Rendering Service.
    Validates template placeholders, renders context dictionaries, and provides default fallback templates.
    """

    ALLOWED_PLACEHOLDERS: Set[str] = {
        'customer_name', 'order_id', 'total', 'prep_time', 'order_type', 'old_status', 'new_status'
    }

    DEFAULT_TEMPLATES: Dict[str, str] = {
        NotificationEvent.ORDER_COMPLETED: "✅ Hi {customer_name}! Your order #{order_id} has been COMPLETED. Thank you for choosing Amazing Foods! 🍔❤️",
        NotificationEvent.ORDER_CANCELLED: "❌ Hi {customer_name}! Your order #{order_id} has been cancelled. Please contact us for assistance.",
        NotificationEvent.ORDER_CREATED: "🎉 Hi {customer_name}! Order #{order_id} received (Rs. {total}). Est. time: {prep_time}."
    }

    @classmethod
    def validate_placeholders(cls, template_text: str) -> Set[str]:
        """
        Extracts all {placeholder} tags and verifies they exist in ALLOWED_PLACEHOLDERS.
        Raises TemplateRenderError if an invalid placeholder is found.
        """
        found_tags = set(re.findall(r'\{([a-zA-Z0-9_]+)\}', template_text))
        invalid_tags = found_tags - cls.ALLOWED_PLACEHOLDERS
        if invalid_tags:
            raise TemplateRenderError(f"Invalid template placeholders found: {', '.join(invalid_tags)}. Allowed: {', '.join(cls.ALLOWED_PLACEHOLDERS)}")
        return found_tags

    @classmethod
    def render(cls, channel: str, event_type: str, context: Dict[str, Any]) -> str:
        """
        Renders template body using context dict. Falls back to DEFAULT_TEMPLATES if DB template is unconfigured.
        """
        # Fetch active DB template with latest version
        db_template = NotificationTemplate.objects.filter(
            channel=channel,
            event_type=event_type,
            is_active=True
        ).order_by('-version').first()

        raw_template = db_template.body_template if db_template else cls.DEFAULT_TEMPLATES.get(event_type, "")

        if not raw_template:
            raw_template = "Notification update for Order #{order_id}."

        # Fill missing context defaults safely
        config = WhatsAppSetting.objects.first()
        default_prep_time = config.estimated_prep_time if config else "25 - 35 mins"

        safe_context = {
            'customer_name': context.get('customer_name') or 'Customer',
            'order_id': context.get('order_id') or 'N/A',
            'total': f"{context.get('total_price', 0):.0f}",
            'prep_time': context.get('prep_time') or default_prep_time,
            'order_type': context.get('order_type') or 'Order',
            'old_status': (context.get('old_status') or '').upper(),
            'new_status': (context.get('new_status') or '').upper(),
        }

        try:
            return raw_template.format(**safe_context)
        except KeyError as e:
            logger.error(f"[TemplateRenderer] Missing context key {e} during rendering event '{event_type}'")
            return f"Update for Order #{safe_context['order_id']}: Status is now {safe_context['new_status']}."
