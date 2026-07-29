from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    path('settings/', views.whatsapp_settings, name='whatsapp_settings'),
]
