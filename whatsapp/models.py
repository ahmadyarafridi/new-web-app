from django.db import models


class WhatsAppCustomer(models.Model):
    STATE_CHOICES = [
        ('IDLE', 'Idle / Welcome'),
        ('WELCOME_BACK', 'Welcome Back (Persistent Cart)'),
        ('MAIN_MENU', 'Browsing Categories'),
        ('BUILDING_ORDER', 'Building Draft Cart'),
        ('EDIT_CART', 'Editing Cart'),
        ('AWAITING_ADDRESS', 'Awaiting Delivery Address'),
        ('AWAITING_NOTES', 'Awaiting Kitchen Notes'),
        ('CONFIRMING_ORDER', 'Confirming Final Order'),
    ]

    phone_number = models.CharField(max_length=30, unique=True, db_index=True, help_text="Digits only e.g. 923232870355")
    name = models.CharField(max_length=120, blank=True, default='')
    default_address = models.TextField(blank=True, default='')
    kitchen_notes = models.TextField(blank=True, default='')
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default='IDLE', db_index=True)
    draft_cart_data = models.JSONField(default=list, blank=True, help_text="Active cart items e.g. [{'product_id': 1, 'name': 'Zinger', 'price': 450, 'qty': 2}]")
    selected_category_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_interaction']
        verbose_name = 'WhatsApp Customer'
        verbose_name_plural = 'WhatsApp Customers'

    def __str__(self):
        return f"{self.name or 'Customer'} ({self.phone_number}) [{self.state}]"

    def clear_draft(self):
        self.state = 'IDLE'
        self.draft_cart_data = []
        self.selected_category_id = None
        self.kitchen_notes = ''
        self.save()


class WhatsAppMessage(models.Model):
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound (From Customer)'),
        ('outbound', 'Outbound (From Assistant)'),
    ]

    STATUS_CHOICES = [
        ('received', 'Received'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]

    message_id = models.CharField(max_length=100, unique=True, db_index=True, help_text="Meta message ID for idempotency")
    customer = models.ForeignKey(WhatsAppCustomer, on_delete=models.CASCADE, related_name='messages')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='inbound')
    body = models.TextField(blank=True, default='')
    raw_payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'WhatsApp Message Log'
        verbose_name_plural = 'WhatsApp Message Logs'

    def __str__(self):
        return f"{self.direction.upper()}: {self.customer.phone_number} - '{self.body[:30]}'"


class WhatsAppSetting(models.Model):
    phone_number_id = models.CharField(max_length=100, blank=True, default='', help_text="Meta Business Phone Number ID")
    access_token = models.TextField(blank=True, default='', help_text="Meta Permanent Access Token")
    verify_token = models.CharField(max_length=100, default='amazing_foods_wa_secret_2026', help_text="Webhook Verify Secret Token")
    app_secret = models.CharField(max_length=100, blank=True, default='', help_text="Meta App Secret for HMAC validation")
    auto_reply_enabled = models.BooleanField(default=True, help_text="Toggle automatic WhatsApp AI replies")
    welcome_message = models.TextField(default="Welcome to Amazing Foods! 🍔\nHow can we serve you today?")
    closed_hours_message = models.TextField(default="Thank you for contacting Amazing Foods! We are currently closed. Please check our opening hours.")
    estimated_prep_time = models.CharField(max_length=50, default="25 - 35 mins", help_text="Estimated preparation time shown in order summary")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'WhatsApp Integration Setting'
        verbose_name_plural = 'WhatsApp Integration Settings'

    def __str__(self) -> str:
        return f"WhatsApp Config (Auto-reply: {'ON' if self.auto_reply_enabled else 'OFF'})"


class NotificationEvent(models.TextChoices):
    ORDER_CREATED = 'order_created', 'Order Created'
    ORDER_PREPARING = 'order_preparing', 'Order Preparing'
    ORDER_READY = 'order_ready', 'Order Ready'
    ORDER_COMPLETED = 'order_completed', 'Order Completed'
    ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'


class NotificationTemplate(models.Model):
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('dashboard', 'Owner Dashboard Bell'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='whatsapp', db_index=True)
    event_type = models.CharField(max_length=50, choices=NotificationEvent.choices, db_index=True)
    body_template = models.TextField(help_text="Template text with placeholders like {customer_name}, {order_id}, {total}, {prep_time}")
    version = models.PositiveIntegerField(default=1, help_text="Template version number for audit tracking")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['channel', 'event_type', '-version']
        verbose_name = 'Notification Template'
        verbose_name_plural = 'Notification Templates'
        constraints = [
            models.UniqueConstraint(fields=['channel', 'event_type', 'version'], name='unique_template_version_per_channel_event')
        ]

    def __str__(self) -> str:
        return f"[{self.channel.upper()}] {self.get_event_type_display()} (v{self.version})"


class NotificationLog(models.Model):
    CHANNEL_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('dashboard', 'Owner Dashboard Bell'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    order = models.ForeignKey('website.Order', on_delete=models.CASCADE, related_name='notification_logs')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, db_index=True)
    provider = models.CharField(max_length=30, default='meta', db_index=True, help_text="Provider e.g. meta, dashboard, twilio, smtp")
    event_type = models.CharField(max_length=50, choices=NotificationEvent.choices, db_index=True)
    attempt_number = models.PositiveIntegerField(default=1, help_text="Delivery attempt sequence number")
    recipient = models.CharField(max_length=100, help_text="Recipient phone number or target identifier")
    rendered_message = models.TextField(help_text="Exact, immutable message text delivered on this attempt")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    provider_message_id = models.CharField(max_length=100, blank=True, default='', db_index=True, help_text="Meta wamid or external message identifier")
    error_message = models.TextField(blank=True, default='', help_text="Error message if attempt failed")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification Delivery Attempt Log'
        verbose_name_plural = 'Notification Delivery Attempt Logs'

    def __str__(self) -> str:
        return f"[{self.provider.upper()}] Order #{self.order.order_id} - {self.event_type} (Attempt #{self.attempt_number}: {self.status})"

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get('force_insert', False):
            raise PermissionError("NotificationLog records are immutable and cannot be updated after creation.")
        super().save(*args, **kwargs)

