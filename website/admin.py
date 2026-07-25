from django.contrib import admin
from .models import RestaurantInfo, Category, Product, Deal, Review, CustomerFeedback, Order, OrderItem

@admin.register(RestaurantInfo)
class RestaurantInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'whatsapp_number', 'email', 'google_rating')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_active')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'tag', 'item_code', 'is_available', 'display_order')
    list_editable = ('price', 'tag', 'is_available', 'display_order')
    list_filter = ('category', 'is_available', 'tag')
    search_fields = ('name', 'item_code', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'tag', 'item_code', 'is_active', 'display_order')
    list_editable = ('price', 'tag', 'is_active', 'display_order')
    list_filter = ('is_active', 'tag')
    search_fields = ('title', 'item_code', 'description')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'reviewer_role', 'is_approved', 'display_order')
    list_editable = ('rating', 'is_approved', 'display_order')
    list_filter = ('rating', 'is_approved')
    search_fields = ('customer_name', 'comment')

@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'rating', 'email', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('customer_name', 'email', 'comment')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'customer_name', 'customer_phone', 'total_price', 'order_status', 'payment_status', 'created_at')
    list_editable = ('order_status', 'payment_status')
    list_filter = ('order_status', 'payment_status', 'created_at')
    search_fields = ('order_id', 'customer_name', 'customer_phone')
    inlines = [OrderItemInline]

