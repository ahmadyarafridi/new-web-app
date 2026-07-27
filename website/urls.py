from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu, name='menu'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('legal/privacy/', views.privacy, name='privacy'),
    path('legal/terms/', views.terms, name='terms'),
    path('privacy/', views.privacy),
    path('privacy-policy/', views.privacy),
    path('terms/', views.terms),
    path('terms-of-service/', views.terms),
    path('create-order/', views.api_create_order, name='create_order'),
    path('api/orders/create/', views.api_create_order, name='api_create_order'),
    path('api/products/', views.api_products, name='api_products'),
]
