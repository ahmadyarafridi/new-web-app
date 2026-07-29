from django.contrib import admin
from .models import (
    WhatsAppCustomer, WhatsAppMessage, WhatsAppSetting,
    NotificationTemplate, NotificationLog
)


@admin.register(WhatsAppCustomer)
class WhatsAppCustomerAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'name', 'state', 'default_address', 'last_interaction')
    list_filter = ('state',)
    search_fields = ('phone_number', 'name', 'default_address')
    ordering = ('-last_interaction',)


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('message_id', 'customer', 'direction', 'status', 'created_at')
    list_filter = ('direction', 'status')
    search_fields = ('message_id', 'customer__phone_number', 'body')
    ordering = ('-created_at',)


@admin.register(WhatsAppSetting)
class WhatsAppSettingAdmin(admin.ModelAdmin):
    list_display = ('phone_number_id', 'auto_reply_enabled', 'updated_at')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('channel', 'event_type', 'version', 'is_active', 'updated_at')
    list_filter = ('channel', 'event_type', 'is_active')
    search_fields = ('body_template',)
    ordering = ('channel', 'event_type', '-version')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'channel', 'provider', 'event_type', 'attempt_number', 'status', 'created_at')
    list_filter = ('channel', 'provider', 'event_type', 'status', 'created_at')
    search_fields = ('order__order_id', 'recipient', 'rendered_message', 'provider_message_id')
    ordering = ('-created_at',)
    readonly_fields = (
        'order', 'channel', 'provider', 'event_type', 'attempt_number',
        'recipient', 'rendered_message', 'status', 'provider_message_id',
        'error_message', 'created_at'
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
