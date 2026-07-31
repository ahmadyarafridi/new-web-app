from django.test import TestCase, TransactionTestCase, Client
from django.db import transaction
from django.contrib.auth.models import User
from website.models import Order, OrderItem, OrderNotification
from whatsapp.models import (
    WhatsAppCustomer, WhatsAppSetting, NotificationTemplate,
    NotificationLog, NotificationEvent
)
from whatsapp.template_renderer import TemplateRenderer, TemplateRenderError
from whatsapp.notification_adapters import WhatsAppAdapter, DashboardBellAdapter, AdapterResult
from whatsapp.notification_engine import NotificationEngine
from website.services.order_service import OrderService


class TemplateRendererTestCase(TestCase):
    """Automated unit tests for TemplateRenderer service."""

    def test_placeholder_validation_valid(self):
        valid_template = "Hi {customer_name}! Order #{order_id} total is Rs. {total}."
        tags = TemplateRenderer.validate_placeholders(valid_template)
        self.assertIn('customer_name', tags)
        self.assertIn('order_id', tags)
        self.assertIn('total', tags)

    def test_placeholder_validation_invalid(self):
        invalid_template = "Hi {cust_name}! Your order {unknown_tag} is ready."
        with self.assertRaises(TemplateRenderError):
            TemplateRenderer.validate_placeholders(invalid_template)

    def test_render_with_fallback(self):
        rendered = TemplateRenderer.render(
            channel='whatsapp',
            event_type=NotificationEvent.ORDER_COMPLETED,
            context={'customer_name': 'Ali', 'order_id': 'WA-101', 'total_price': 850}
        )
        self.assertIn('Ali', rendered)
        self.assertIn('WA-101', rendered)
        self.assertIn('COMPLETED', rendered)


class NotificationLogImmutabilityTestCase(TestCase):
    """Automated unit tests for NotificationLog model-level immutability."""

    def setUp(self):
        self.order = Order.objects.create(
            order_id="WA-IMMUTABLE-01",
            customer_name="Immutable User",
            customer_phone="923232870355",
            total_price=500,
            order_status="pending"
        )
        self.log = NotificationLog.objects.create(
            order=self.order,
            channel="whatsapp",
            provider="meta",
            event_type=NotificationEvent.ORDER_COMPLETED,
            attempt_number=1,
            recipient="923232870355",
            rendered_message="Test Body",
            status="sent"
        )

    def test_notification_log_immutability(self):
        self.log.status = "failed"
        with self.assertRaises(PermissionError):
            self.log.save()


class TemplateVersioningTestCase(TestCase):
    """Automated unit tests for NotificationTemplate versioning."""

    def test_template_versioning_increments(self):
        t1 = NotificationTemplate.objects.create(
            channel='whatsapp',
            event_type=NotificationEvent.ORDER_COMPLETED,
            body_template="Version 1: Hi {customer_name}",
            version=1,
            is_active=True
        )

        t1.is_active = False
        t1.save()

        t2 = NotificationTemplate.objects.create(
            channel='whatsapp',
            event_type=NotificationEvent.ORDER_COMPLETED,
            body_template="Version 2: Hello {customer_name}",
            version=2,
            is_active=True
        )

        rendered = TemplateRenderer.render(
            channel='whatsapp',
            event_type=NotificationEvent.ORDER_COMPLETED,
            context={'customer_name': 'Sarah'}
        )
        self.assertIn('Version 2', rendered)


class NotificationEngineTestCase(TestCase):
    """Automated unit tests for NotificationEngine and adapters."""

    def setUp(self):
        self.order = Order.objects.create(
            order_id="WA-TEST-001",
            customer_name="Test User",
            customer_phone="923232870355",
            delivery_address="Test Address",
            total_price=1200,
            order_status="pending"
        )

    def test_whatsapp_adapter_creates_notification_log(self):
        adapter = WhatsAppAdapter()
        res: AdapterResult = adapter.send(
            order=self.order,
            event_type=NotificationEvent.ORDER_COMPLETED,
            context={'customer_name': 'Test User', 'order_id': 'WA-TEST-001', 'new_status': 'completed'}
        )
        self.assertTrue(res.success)
        self.assertEqual(res.channel, 'whatsapp')
        self.assertEqual(res.provider, 'meta')

        log = NotificationLog.objects.filter(order=self.order, channel='whatsapp', event_type=NotificationEvent.ORDER_COMPLETED).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.attempt_number, 1)
        self.assertEqual(log.status, 'sent')
        self.assertIn('Test User', log.rendered_message)

    def test_dashboard_bell_adapter_creates_ordernotification(self):
        adapter = DashboardBellAdapter()
        res: AdapterResult = adapter.send(
            order=self.order,
            event_type=NotificationEvent.ORDER_COMPLETED,
            context={'customer_name': 'Test User', 'order_id': 'WA-TEST-001', 'new_status': 'completed'}
        )
        self.assertTrue(res.success)
        self.assertEqual(res.channel, 'dashboard')

        notif = OrderNotification.objects.filter(order=self.order).first()
        self.assertIsNotNone(notif)
        self.assertFalse(notif.is_read)

    def test_engine_idempotency_suppression(self):
        payload = {
            'order': self.order,
            'customer_name': self.order.customer_name,
            'order_id': self.order.order_id,
            'new_status': 'completed'
        }
        res1 = NotificationEngine.dispatch(NotificationEvent.ORDER_COMPLETED, payload)
        self.assertTrue(res1['whatsapp'].success)

        res2 = NotificationEngine.dispatch(NotificationEvent.ORDER_COMPLETED, payload)
        self.assertTrue(res2['whatsapp'].success)
        self.assertIn("Duplicate suppressed", res2['whatsapp'].error)


class OrderServiceTransactionTestCase(TransactionTestCase):
    """Automated unit tests for OrderService status updates & transaction.on_commit callback."""

    def setUp(self):
        self.user = User.objects.create_superuser('admin_user', 'admin@example.com', 'password123')
        self.client = Client()
        self.client.login(username='admin_user', password='password123')

    def test_order_service_update_status_dispatches_on_commit(self):
        order = Order.objects.create(
            order_id="WA-TEST-002",
            customer_name="John Doe",
            customer_phone="923001234567",
            delivery_address="Main Street",
            total_price=950,
            order_status="pending"
        )

        with transaction.atomic():
            updated_order = OrderService.update_status(order, "completed", updated_by="admin_test")
            self.assertEqual(updated_order.order_status, "completed")

        logs = NotificationLog.objects.filter(order=order)
        self.assertGreaterEqual(logs.count(), 1)

        wa_log = logs.filter(channel='whatsapp', event_type=NotificationEvent.ORDER_COMPLETED).first()
        self.assertIsNotNone(wa_log)
        self.assertEqual(wa_log.status, 'sent')

    def test_dashboard_view_triggers_order_service(self):
        from django.urls import reverse
        order = Order.objects.create(
            order_id="WA-DASH-01",
            customer_name="Dash Customer",
            customer_phone="923232870000",
            total_price=1500,
            order_status="pending"
        )
        url = reverse('order_update_status', args=[order.pk])
        res = self.client.post(url, {'order_status': 'completed'})
        self.assertEqual(res.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.order_status, 'completed')

        logs = NotificationLog.objects.filter(order=order)
        self.assertGreaterEqual(logs.count(), 1)


import hmac
import hashlib
import json

class WebhookSignatureTestCase(TestCase):
    """Automated unit tests for Meta Webhook HMAC SHA-256 signature verification."""

    def setUp(self):
        self.secret = "test_meta_app_secret_12345"
        WhatsAppSetting.objects.create(
            phone_number_id="1319137847940310",
            access_token="EAAP_TEST_TOKEN",
            app_secret=self.secret,
            verify_token="test_verify_token"
        )
        self.payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "2464752690672704",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "15556691242", "phone_number_id": "1319137847940310"},
                        "messages": [{
                            "from": "923232870355",
                            "id": "wamid.HBgMOTIzMjMyODcwMzU1FQIAEhggMTIzNDU2Nzg5MAA=",
                            "timestamp": "1722300000",
                            "text": {"body": "Hi"},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        self.raw_body = json.dumps(self.payload).encode('utf-8')

    def test_valid_signature_accepted(self):
        calculated_hash = hmac.new(
            self.secret.encode('utf-8'),
            msg=self.raw_body,
            digestmod=hashlib.sha256
        ).hexdigest()

        response = self.client.post(
            '/whatsapp/webhook/',
            data=self.raw_body,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=f"sha256={calculated_hash}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), 'EVENT_RECEIVED')

    def test_invalid_signature_rejected(self):
        bad_hash = "sha256=" + "0" * 64
        response = self.client.post(
            '/whatsapp/webhook/',
            data=self.raw_body,
            content_type='application/json',
            HTTP_X_HUB_SIGNATURE_256=bad_hash
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode('utf-8'), 'Invalid Signature')

    def test_missing_signature_rejected(self):
        response = self.client.post(
            '/whatsapp/webhook/',
            data=self.raw_body,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode('utf-8'), 'Invalid Signature')
