import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import WhatsAppSetting, WhatsAppCustomer, WhatsAppMessage
from .webhook import verify_signature, extract_incoming_message

logger = logging.getLogger(__name__)


@csrf_exempt
def whatsapp_webhook(request):
    """
    Production-ready, idempotent Meta Webhook handler.
    GET: Responds to Meta verification challenge.
    POST: Validates HMAC-SHA256 signature, enforces message_id idempotency, logs message, returns 200 OK.
    """
    # 1. GET Request: Meta Webhook Verification Challenge
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')

        expected_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
        if not expected_token:
            config = WhatsAppSetting.objects.first()
            expected_token = config.verify_token if config else 'amazing_foods_wa_secret_2026'

        if mode == 'subscribe' and token == expected_token:
            logger.info("[Meta Webhook] Successfully verified GET challenge!")
            return HttpResponse(challenge, status=200)
        else:
            logger.warning("[Meta Webhook] GET verification failed: token mismatch")
            return HttpResponse('Forbidden', status=403)

    # 2. POST Request: Meta Event Notification
    elif request.method == 'POST':
        signature = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
        if not verify_signature(request.body, signature):
            logger.warning("[Meta Webhook] Invalid HMAC SHA-256 signature")
            return HttpResponse('Invalid Signature', status=403)

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON', status=400)

        parsed_msg = extract_incoming_message(payload)
        if not parsed_msg:
            # Event was status/receipt update (sent/delivered/read), return 200 OK to Meta
            logger.info(f"[Meta Webhook] Received status/receipt event from Meta.")
            return HttpResponse('EVENT_RECEIVED', status=200)

        logger.info(f"[Meta Webhook] Processing message from '{parsed_msg['sender_phone']}' ({parsed_msg['sender_name']}): '{parsed_msg['text_body']}'")

        # Idempotency check: drop if message_id already processed
        msg_id = parsed_msg['message_id']
        if WhatsAppMessage.objects.filter(message_id=msg_id).exists():
            logger.info(f"[Meta Webhook] Duplicate message_id '{msg_id}' dropped.")
            return HttpResponse('EVENT_RECEIVED', status=200)

        # Log inbound message
        customer, _ = WhatsAppCustomer.objects.get_or_create(
            phone_number=parsed_msg['sender_phone'],
            defaults={'name': parsed_msg['sender_name']}
        )
        WhatsAppMessage.objects.create(
            message_id=msg_id,
            customer=customer,
            direction='inbound',
            body=parsed_msg['text_body'],
            raw_payload=payload,
            status='received'
        )

        # Trigger State Machine processing for auto-reply
        config = WhatsAppSetting.objects.first()
        auto_reply = config.auto_reply_enabled if config else True

        if auto_reply and parsed_msg['text_body']:
            from .state_machine import WhatsAppStateMachine
            from .services import WhatsAppService
            from website.models import Category
            from website.views import ensure_db_ready

            if Category.objects.count() == 0:
                ensure_db_ready()

            try:
                reply_res = WhatsAppStateMachine.process_incoming(
                    sender_phone=parsed_msg['sender_phone'],
                    sender_name=parsed_msg['sender_name'],
                    message_text=parsed_msg['text_body'],
                    interactive_id=parsed_msg.get('interactive_id')
                )
                logger.info(f"[Meta Webhook] State machine replied to {parsed_msg['sender_phone']}")
            except Exception as e:
                logger.error(f"[Meta Webhook StateMachine Error] {e}", exc_info=True)
                WhatsAppService.send_text_message(
                    parsed_msg['sender_phone'],
                    "Welcome to Amazing Foods! 🍔✨\n\nReply *menu* anytime to browse items and place an order!"
                )

        return HttpResponse('EVENT_RECEIVED', status=200)

    return HttpResponse('Method Not Allowed', status=405)


def whatsapp_settings(request):
    """
    Owner Dashboard View to manage WhatsApp API credentials and versioned Notification Templates.
    Validates placeholders fail-fast before saving and creates new template versions when edited.
    """
    from django.contrib.auth.decorators import login_required
    from django.contrib import messages
    from django.shortcuts import render, redirect
    from .models import NotificationTemplate, NotificationEvent

    if not request.user.is_authenticated:
        return redirect('login')

    config, _ = WhatsAppSetting.objects.get_or_create(id=1)

    if request.method == 'POST':
        config.phone_number_id = request.POST.get('phone_number_id', '').strip()
        config.access_token = request.POST.get('access_token', '').strip()
        config.verify_token = request.POST.get('verify_token', '').strip()
        config.app_secret = request.POST.get('app_secret', '').strip()
        config.auto_reply_enabled = 'auto_reply_enabled' in request.POST
        config.estimated_prep_time = request.POST.get('estimated_prep_time', '25 - 35 mins').strip()
        config.save()

        # Update templates safely with validation & versioning
        for event_key, _ in NotificationEvent.choices:
            tpl_input = request.POST.get(f'template_{event_key}', '').strip()
            if tpl_input:
                try:
                    from .template_renderer import TemplateRenderer
                    TemplateRenderer.validate_placeholders(tpl_input)

                    active_tpl = NotificationTemplate.objects.filter(
                        channel='whatsapp',
                        event_type=event_key,
                        is_active=True
                    ).order_by('-version').first()

                    if not active_tpl or active_tpl.body_template != tpl_input:
                        new_ver = (active_tpl.version + 1) if active_tpl else 1
                        if active_tpl:
                            active_tpl.is_active = False
                            active_tpl.save(update_fields=['is_active'])

                        NotificationTemplate.objects.create(
                            channel='whatsapp',
                            event_type=event_key,
                            body_template=tpl_input,
                            version=new_ver,
                            is_active=True
                        )
                except Exception as e:
                    messages.error(request, f"Error in template '{event_key}': {e}")
                    return redirect('whatsapp_settings')

        messages.success(request, "WhatsApp Integration & Notification settings updated successfully!")
        return redirect('whatsapp_settings')

    templates = {}
    for event_key, event_label in NotificationEvent.choices:
        active_tpl = NotificationTemplate.objects.filter(channel='whatsapp', event_type=event_key, is_active=True).order_by('-version').first()
        from .template_renderer import TemplateRenderer
        default_body = TemplateRenderer.DEFAULT_TEMPLATES.get(event_key, "")
        templates[event_key] = {
            'label': event_label,
            'body': active_tpl.body_template if active_tpl else default_body,
            'version': active_tpl.version if active_tpl else 1
        }

    return render(request, 'accounts/whatsapp_settings.html', {
        'config': config,
        'templates': templates
    })
