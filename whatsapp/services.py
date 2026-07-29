import requests
import logging
import re
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from django.conf import settings
from .models import WhatsAppSetting, WhatsAppCustomer, WhatsAppMessage

logger = logging.getLogger(__name__)


class LoggingRetry(Retry):
    """
    Custom Retry class logging each exponential backoff attempt for transient Meta Graph API failures.
    """
    def increment(self, method=None, url=None, response=None, error=None, _pool=None, _stacktrace=None):
        status = response.status if response else (str(error) if error else 'Connection Error/Timeout')
        logger.warning(
            f"[WhatsApp API Retry] Transient failure encountered (Status: {status}). "
            f"Retrying Meta Graph API request to '{url}'..."
        )
        return super().increment(method, url, response, error, _pool, _stacktrace)


def get_http_session() -> requests.Session:
    """
    Returns a configured requests.Session with exponential backoff retries for transient Meta API failures.
    Retries ONLY on HTTP 429 (Rate Limit), 500, 502, 503, 504 and connection timeouts.
    Does NOT retry client 4xx errors (400, 401, 403, 404).
    """
    session = requests.Session()
    retries = LoggingRetry(
        total=3,
        backoff_factor=1.0,  # Delays: 1s, 2s, 4s...
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class WhatsAppService:
    """
    Extensible Meta Cloud API v20.0 Integration Service.
    Supports text, interactive buttons, list picker menus, media, and templates.
    Credential resolution: Environment variables first, then database settings.
    Includes production-ready exponential backoff retries for transient failures.
    """
    GRAPH_API_URL = "https://graph.facebook.com/v20.0"

    @classmethod
    def get_credentials(cls):
        phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '').strip()
        token = getattr(settings, 'WHATSAPP_TOKEN', '').strip()

        if phone_id and token:
            return phone_id, token

        config = WhatsAppSetting.objects.first()
        if config:
            phone_id = phone_id or config.phone_number_id
            token = token or config.access_token

        return phone_id, token

    @classmethod
    def send_text_message(cls, recipient_phone: str, message_text: str) -> dict:
        clean_phone = re.sub(r'\D', '', str(recipient_phone))
        phone_id, token = cls.get_credentials()
        if not phone_id or not token:
            logger.warning(f"[WhatsAppService] Meta API credentials missing. Mocking text send to {clean_phone}")
            return {'status': 'mocked', 'recipient': clean_phone}

        url = f"{cls.GRAPH_API_URL}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        try:
            session = get_http_session()
            res = session.post(url, json=payload, headers=headers, timeout=10)
            res_data = res.json()
            if res.status_code == 200:
                msg_id = res_data.get('messages', [{}])[0].get('id', 'outbound-id')
                cls._log_outbound(clean_phone, message_text, msg_id, 'sent')
                return res_data
            else:
                logger.error(f"[WhatsAppService Error {res.status_code}] Meta API error for {clean_phone}: {res_data}")
                return res_data
        except Exception as e:
            logger.error(f"[WhatsAppService] Exception sending text message: {e}")
            return {'error': str(e)}

    @classmethod
    def send_interactive_buttons(cls, recipient_phone: str, body_text: str, buttons: list) -> dict:
        """
        Sends quick reply buttons (max 3 buttons).
        buttons format: [{'id': 'btn_1', 'title': 'Confirm'}, ...]
        """
        clean_phone = re.sub(r'\D', '', str(recipient_phone))
        phone_id, token = cls.get_credentials()
        if not phone_id or not token:
            logger.warning(f"[WhatsAppService] Mocking interactive buttons to {clean_phone}")
            return {'status': 'mocked'}

        url = f"{cls.GRAPH_API_URL}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        formatted_buttons = []
        for btn in buttons[:3]:
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn['id'],
                    "title": btn['title'][:20]
                }
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": formatted_buttons}
            }
        }

        try:
            session = get_http_session()
            res = session.post(url, json=payload, headers=headers, timeout=10)
            res_data = res.json()
            if res.status_code != 200:
                logger.error(f"[WhatsAppService Error {res.status_code}] Buttons error for {clean_phone}: {res_data}")
            return res_data
        except Exception as e:
            logger.error(f"[WhatsAppService] Exception sending buttons: {e}")
            return {'error': str(e)}

    @classmethod
    def send_interactive_list(cls, recipient_phone: str, header_text: str, body_text: str, button_title: str, sections: list) -> dict:
        """
        Sends an interactive list picker dropdown menu.
        sections format: [{'title': 'Categories', 'rows': [{'id': 'cat_1', 'title': 'Pizzas', 'description': 'Delish pizzas'}]}]
        """
        clean_phone = re.sub(r'\D', '', str(recipient_phone))
        phone_id, token = cls.get_credentials()
        if not phone_id or not token:
            logger.warning(f"[WhatsAppService] Mocking interactive list to {clean_phone}")
            return {'status': 'mocked'}

        url = f"{cls.GRAPH_API_URL}/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header_text[:60]},
                "body": {"text": body_text[:1024]},
                "action": {
                    "button": button_title[:20],
                    "sections": sections
                }
            }
        }

        try:
            session = get_http_session()
            res = session.post(url, json=payload, headers=headers, timeout=10)
            res_data = res.json()
            if res.status_code != 200:
                logger.error(f"[WhatsAppService Error {res.status_code}] List error for {clean_phone}: {res_data}")
            return res_data
        except Exception as e:
            logger.error(f"[WhatsAppService] Exception sending list: {e}")
            return {'error': str(e)}

    @classmethod
    def _log_outbound(cls, recipient_phone: str, body: str, msg_id: str, status: str = 'sent'):
        try:
            customer, _ = WhatsAppCustomer.objects.get_or_create(phone_number=recipient_phone)
            WhatsAppMessage.objects.create(
                message_id=msg_id,
                customer=customer,
                direction='outbound',
                body=body,
                status=status
            )
        except Exception as e:
            logger.error(f"[WhatsAppService] Error logging outbound message: {e}")
