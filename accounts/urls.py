from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.owner_login, name='login'),
    path('logout/', views.owner_logout, name='logout'),
    
    # Dashboard Main Overview
    path('dashboard/', views.owner_dashboard, name='dashboard'),
    path('dashboard/status/toggle/', views.toggle_restaurant_status, name='toggle_restaurant_status'),
    
    # Orders Management
    path('dashboard/orders/', views.manage_orders, name='manage_orders'),
    path('dashboard/orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('dashboard/orders/<int:pk>/status/', views.order_update_status, name='order_update_status'),
    path('dashboard/orders/<int:pk>/complete/', views.order_complete, name='order_complete'),
    path('dashboard/orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    
    # Products Management
    path('dashboard/products/', views.manage_products, name='manage_products'),
    path('dashboard/products/detail/<int:pk>/', views.product_detail, name='product_detail'),
    path('dashboard/products/add/', views.product_add, name='product_add'),
    path('dashboard/products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('dashboard/products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('dashboard/products/toggle/<int:pk>/', views.product_toggle, name='product_toggle'),
    
    # Categories Management
    path('dashboard/categories/', views.manage_categories, name='manage_categories'),
    path('dashboard/categories/add/', views.category_add, name='category_add'),
    path('dashboard/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('dashboard/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    
    # Deals Management
    path('dashboard/deals/', views.manage_deals, name='manage_deals'),
    path('dashboard/deals/add/', views.deal_add, name='deal_add'),
    path('dashboard/deals/edit/<int:pk>/', views.deal_edit, name='deal_edit'),
    path('dashboard/deals/delete/<int:pk>/', views.deal_delete, name='deal_delete'),
    
    # Reviews Management
    path('dashboard/reviews/', views.manage_reviews, name='manage_reviews'),
    path('dashboard/reviews/add/', views.review_add, name='review_add'),
    path('dashboard/reviews/edit/<int:pk>/', views.review_edit, name='review_edit'),
    path('dashboard/reviews/delete/<int:pk>/', views.review_delete, name='review_delete'),
    path('dashboard/reviews/toggle/<int:pk>/', views.review_toggle, name='review_toggle'),
    
    # Restaurant Settings & Export
    path('dashboard/settings/', views.manage_settings, name='manage_settings'),
    path('dashboard/export-full-zip/', views.export_full_data_zip, name='export_full_data_zip'),
    
    # Customer Feedback Management
    path('dashboard/feedback/', views.manage_feedback, name='manage_feedback'),
    path('dashboard/feedback/approve/<int:pk>/', views.feedback_approve, name='feedback_approve'),
    path('dashboard/feedback/reject/<int:pk>/', views.feedback_reject, name='feedback_reject'),
    path('dashboard/feedback/delete/<int:pk>/', views.feedback_delete, name='feedback_delete'),
    
    # Notifications API
    path('dashboard/notifications/api/', views.api_get_notifications, name='api_get_notifications'),
    path('dashboard/notifications/read/<int:pk>/', views.api_mark_notification_read, name='api_mark_notification_read'),
    path('dashboard/notifications/read-all/', views.api_mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('dashboard/notifications/delete/<int:pk>/', views.api_delete_notification, name='api_delete_notification'),

    # Detailed Analytics Pages & CSV Exporters
    path('dashboard/analytics/visitors/', views.analytics_visitors, name='analytics_visitors'),
    path('dashboard/analytics/visitors/today/', views.analytics_visitors_today, name='analytics_visitors_today'),
    path('dashboard/analytics/visitors/week/', views.analytics_visitors_week, name='analytics_visitors_week'),
    path('dashboard/analytics/visitors/month/', views.analytics_visitors_month, name='analytics_visitors_month'),
    path('dashboard/analytics/visitors/year/', views.analytics_visitors_year, name='analytics_visitors_year'),
    path('dashboard/analytics/visitors/export/', views.export_visitors_csv, name='export_visitors_csv'),
    path('dashboard/analytics/revenue/', views.analytics_revenue, name='analytics_revenue'),
    path('dashboard/analytics/revenue/today/', views.analytics_revenue_today, name='analytics_revenue_today'),
    path('dashboard/analytics/revenue/week/', views.analytics_revenue_week, name='analytics_revenue_week'),
    path('dashboard/analytics/revenue/month/', views.analytics_revenue_month, name='analytics_revenue_month'),
    path('dashboard/analytics/revenue/year/', views.analytics_revenue_year, name='analytics_revenue_year'),
    path('dashboard/analytics/revenue/export/', views.export_revenue_csv, name='export_revenue_csv'),
    path('dashboard/analytics/orders/', views.analytics_orders, name='analytics_orders'),
    path('dashboard/analytics/orders/today/', views.analytics_orders_today, name='analytics_orders_today'),
    path('dashboard/analytics/orders/today/pending/', views.analytics_orders_today_pending, name='analytics_orders_today_pending'),
    path('dashboard/analytics/orders/today/completed/', views.analytics_orders_today_completed, name='analytics_orders_today_completed'),
    path('dashboard/analytics/orders/week/', views.analytics_orders_week, name='analytics_orders_week'),
    path('dashboard/analytics/orders/month/', views.analytics_orders_month, name='analytics_orders_month'),
    path('dashboard/analytics/orders/year/', views.analytics_orders_year, name='analytics_orders_year'),
    path('dashboard/analytics/orders/export/', views.export_orders_csv, name='export_orders_csv'),
]
