from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.menu, name='menu'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('create-order/', views.api_create_order, name='create_order'),
    path('api/orders/create/', views.api_create_order, name='api_create_order'),
    path('api/products/', views.api_products, name='api_products'),
]
