import hmac
import hashlib
import json
import logging
from django.conf import settings
from .models import WhatsAppSetting

logger = logging.getLogger(__name__)


def verify_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Validates X-Hub-Signature-256 header sent by Meta Webhook.
    Uses WHATSAPP_APP_SECRET from environment variables first, then database settings.
    Strict enforcement: In production (DEBUG=False), signature bypass is NEVER allowed.
    """
    app_secret = getattr(settings, 'WHATSAPP_APP_SECRET', '')
    if not app_secret:
        config = WhatsAppSetting.objects.first()
        app_secret = config.app_secret if config else ''

    if not app_secret:
        if getattr(settings, 'DEBUG', True):
            logger.warning("[Meta Webhook] DEBUG=True and WHATSAPP_APP_SECRET is unset. Bypassing HMAC check for local dev testing.")
            return True
        else:
            logger.critical("[Meta Webhook SECURITY ERROR] DEBUG=False but WHATSAPP_APP_SECRET is unconfigured! Rejecting request.")
            return False

    if not signature_header or not signature_header.startswith('sha256='):
        logger.warning("[Meta Webhook] Missing or malformed X-Hub-Signature-256 header.")
        return False

    try:
        expected_hash = signature_header.split('sha256=')[1]
        calculated_hash = hmac.new(
            app_secret.encode('utf-8'),
            msg=raw_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_hash, calculated_hash)
    except Exception as e:
        logger.error(f"[Meta Webhook] HMAC comparison error: {e}")
        return False


def extract_incoming_message(data: dict) -> dict:
    """
    Parses Meta Webhook POST payload to extract incoming message details.
    Extensible for text, interactive buttons, list replies, media, and template status receipts.
    """
    try:
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])

        if not messages:
            return None

        msg = messages[0]
        contacts = value.get('contacts', [])
        sender_name = contacts[0].get('profile', {}).get('name', '') if contacts else ''

        msg_type = msg.get('type', 'text')
        text_body = ''
        interactive_id = None
        media_url = None

        if msg_type == 'text':
            text_body = msg.get('text', {}).get('body', '').strip()
        elif msg_type == 'interactive':
            interactive_type = msg.get('interactive', {}).get('type')
            if interactive_type == 'button_reply':
                interactive_id = msg.get('interactive', {}).get('button_reply', {}).get('id')
                text_body = msg.get('interactive', {}).get('button_reply', {}).get('title')
            elif interactive_type == 'list_reply':
                interactive_id = msg.get('interactive', {}).get('list_reply', {}).get('id')
                text_body = msg.get('interactive', {}).get('list_reply', {}).get('title')
        elif msg_type == 'image':
            text_body = msg.get('image', {}).get('caption', '[Image Message]')
            media_url = msg.get('image', {}).get('id')

        return {
            'message_id': msg.get('id'),
            'sender_phone': msg.get('from'),
            'sender_name': sender_name,
            'text_body': text_body,
            'msg_type': msg_type,
            'interactive_id': interactive_id,
            'media_url': media_url,
            'timestamp': msg.get('timestamp')
        }
    except Exception as e:
        logger.error(f"[Meta Webhook Parser] Error parsing payload: {e}")
        return None
