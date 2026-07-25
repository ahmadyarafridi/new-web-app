import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from website.models import RestaurantInfo, Category, Product, Deal, Review, CustomerFeedback, Order, OrderItem, DailyVisit, OrderNotification
from .forms import (
    OwnerLoginForm, ProductForm, CategoryForm,
    DealForm, ReviewForm, RestaurantInfoForm
)
from .analytics_utils import (
    get_visitor_analytics_data,
    get_revenue_analytics_data,
    get_orders_analytics_data,
)

def owner_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = OwnerLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = OwnerLoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required(login_url='login')
def owner_logout(request):
    auth_logout(request)
    return redirect('index')


@login_required(login_url='login')
def toggle_restaurant_status(request):
    if request.method == 'POST':
        info = RestaurantInfo.objects.first()
        if not info:
            info = RestaurantInfo.objects.create()
        info.is_open = not info.is_open
        info.save()
    return redirect('dashboard')


@login_required(login_url='login')
def owner_dashboard(request):
    today = timezone.now().date()

    # 1. Total Visits (per day)
    visit_obj = DailyVisit.objects.filter(date=today).first()
    today_visits = visit_obj.count if visit_obj else 0

    # 2. Orders Booked (Total completed orders)
    orders_booked = Order.objects.filter(order_status='completed').count()
    today_orders_count = Order.objects.filter(created_at__date=today).count()

    # 3. Total Income (price of completed items sold in a day)
    income_aggregate = Order.objects.filter(order_status='completed', created_at__date=today).aggregate(total=Sum('total_price'))
    today_income = income_aggregate['total'] or 0

    # 4. Total Products (items in menu)
    total_products = Product.objects.count()
    available_products = Product.objects.filter(is_available=True).count()
    out_of_stock_products = Product.objects.filter(is_available=False).count()
    total_categories = Category.objects.count()

    context = {
        'today_visits': today_visits,
        'orders_booked': orders_booked,
        'today_orders_count': today_orders_count,
        'today_income': today_income,
        'total_products': total_products,
        'available_products': available_products,
        'out_of_stock_products': out_of_stock_products,
        'total_categories': total_categories,
        'recent_orders': Order.objects.all()[:5],
        'recent_notifications': OrderNotification.objects.select_related('order').all()[:5],
    }
    return render(request, 'accounts/dashboard.html', context)


# ==============================================================================
# ORDERS MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_orders(request):
    status_filter = request.GET.get('status', 'all').strip()
    search_query = request.GET.get('q', '').strip()

    orders_qs = Order.objects.prefetch_related('items').all()

    if status_filter in ['pending', 'preparing', 'ready', 'completed', 'cancelled']:
        orders_qs = orders_qs.filter(order_status=status_filter)

    if search_query:
        orders_qs = orders_qs.filter(
            Q(order_id__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_phone__icontains=search_query) |
            Q(delivery_address__icontains=search_query)
        )

    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'current_status': status_filter,
        'search_query': search_query,
        'all_count': Order.objects.count(),
        'pending_count': Order.objects.filter(order_status='pending').count(),
        'preparing_count': Order.objects.filter(order_status='preparing').count(),
        'ready_count': Order.objects.filter(order_status='ready').count(),
        'completed_count': Order.objects.filter(order_status='completed').count(),
        'cancelled_count': Order.objects.filter(order_status='cancelled').count(),
        'analytics': get_orders_analytics_data(),
    }
    return render(request, 'accounts/orders.html', context)


import urllib.parse

@login_required(login_url='login')
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    info = RestaurantInfo.objects.first()
    rest_name = info.name if info else "Delicious Food Stop"

    # Build formatted WhatsApp response message
    items = order.items.all()
    if items.exists():
        formatted_items = [f"{idx+1}. {item.product_name} x{item.quantity} - Rs. {item.subtotal:.0f}" for idx, item in enumerate(items)]
        items_list_str = "\n".join(formatted_items)
    else:
        items_list_str = f"1. {order.items_summary}"

    wa_msg = (
        f"Hi *{order.customer_name}*! This is *{rest_name}* regarding your order.\n\n"
        f"------------------------------\n"
        f"*Ordered Items:*\n"
        f"{items_list_str}\n"
        f"------------------------------\n"
        f"*Total Amount:* Rs. {order.total_price:.0f}\n"
        f"------------------------------\n\n"
        f"Should we confirm and start preparing your order?"
    )
    
    encoded_wa_msg = urllib.parse.quote(wa_msg)
    clean_phone = "".join(c for c in (order.customer_phone or '') if c.isdigit())
    wa_url = f"https://wa.me/{clean_phone}?text={encoded_wa_msg}"

    return render(request, 'accounts/order_detail.html', {
        'order': order,
        'restaurant_info': info,
        'wa_url': wa_url,
    })


@login_required(login_url='login')
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('order_status')
        new_payment = request.POST.get('payment_status')

        if new_status in dict(Order.STATUS_CHOICES):
            order.order_status = new_status

        if new_payment in dict(Order.PAYMENT_CHOICES):
            order.payment_status = new_payment

        order.save()
    return redirect('order_detail', pk=pk)


@login_required(login_url='login')
def order_complete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.order_status = 'completed'
        order.payment_status = 'paid'
        order.save()
    return redirect('analytics_orders_today')


@login_required(login_url='login')
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST':
        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect('analytics_orders_today')
    return render(request, 'accounts/confirm_delete.html', {'object_name': f"Order #{order.order_id}", 'type': 'Order', 'cancel_url': 'analytics_orders_today'})


# ==============================================================================
# PRODUCTS MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_products(request):
    from django.db.models import Count
    search_query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('cat', '').strip()

    categories_list = Category.objects.annotate(product_count=Count('products')).order_by('display_order', 'name')
    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()

    products_qs = Product.objects.select_related('category').all()

    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(item_code__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tag__icontains=search_query)
        )

    if category_slug:
        products_qs = products_qs.filter(category__slug=category_slug)

    paginator = Paginator(products_qs, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'categories': categories_list,
        'selected_category': selected_category,
        'search_query': search_query,
        'current_category': category_slug,
    }
    return render(request, 'accounts/products.html', context)


@login_required(login_url='login')
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    return render(request, 'accounts/product_detail.html', {'product': product})


@login_required(login_url='login')
def product_add(request):
    from django.urls import reverse
    cat_slug = request.GET.get('cat', '').strip()
    initial_data = {}
    if cat_slug:
        cat_obj = Category.objects.filter(slug=cat_slug).first()
        if cat_obj:
            initial_data['category'] = cat_obj.pk

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            return redirect(f"{reverse('manage_products')}?cat={product.category.slug}")
    else:
        form = ProductForm(initial=initial_data)
    return render(request, 'accounts/product_form.html', {'form': form, 'title': 'Add New Product'})


@login_required(login_url='login')
def product_edit(request, pk):
    from django.urls import reverse
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            return redirect(f"{reverse('manage_products')}?cat={product.category.slug}")
    else:
        form = ProductForm(instance=product)
    return render(request, 'accounts/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})


@login_required(login_url='login')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        cat_slug = product.category.slug if product.category else ''
        product.delete()
        messages.success(request, f'Product "{name}" deleted successfully.')
        return redirect(f"{reverse('manage_products')}?cat={cat_slug}" if cat_slug else 'manage_products')
    return render(request, 'accounts/confirm_delete.html', {'object_name': product.name, 'type': 'Product', 'cancel_url': 'manage_products'})


@login_required(login_url='login')
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_available = not product.is_available
    product.save()
    status = "Available" if product.is_available else "Unavailable"
    messages.success(request, f'Product "{product.name}" is now {status}.')
    return redirect('manage_products')


# ==============================================================================
# CATEGORIES MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_categories(request):
    return redirect('manage_products')


@login_required(login_url='login')
def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('manage_products')
    else:
        form = CategoryForm()
    return render(request, 'accounts/category_form.html', {'form': form, 'title': 'Add New Category'})


@login_required(login_url='login')
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('manage_products')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'accounts/category_form.html', {'form': form, 'title': 'Edit Category', 'category': category})


@login_required(login_url='login')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        # SAFETY CHECK: Only empty categories can be deleted
        item_count = category.products.count()
        if item_count > 0:
            messages.error(
                request,
                f'Cannot delete category "{category.name}" because it contains {item_count} product(s). Please move or delete the products inside first.'
            )
            return redirect('manage_products')

        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully.')
        return redirect('manage_products')

    return render(request, 'accounts/confirm_delete.html', {'object_name': category.name, 'type': 'Category', 'cancel_url': 'manage_products'})


# ==============================================================================
# DEALS MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_deals(request):
    search_query = request.GET.get('q', '').strip()
    deals_qs = Deal.objects.all()

    if search_query:
        deals_qs = deals_qs.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query) | Q(item_code__icontains=search_query)
        )

    paginator = Paginator(deals_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/deals.html', {'deals': page_obj, 'search_query': search_query})


@login_required(login_url='login')
def deal_add(request):
    if request.method == 'POST':
        form = DealForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deal added successfully!')
            return redirect('manage_deals')
    else:
        form = DealForm()
    return render(request, 'accounts/deal_form.html', {'form': form, 'title': 'Add New Deal'})


@login_required(login_url='login')
def deal_edit(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        form = DealForm(request.POST, request.FILES, instance=deal)
        if form.is_valid():
            form.save()
            messages.success(request, f'Deal "{deal.title}" updated successfully!')
            return redirect('manage_deals')
    else:
        form = DealForm(instance=deal)
    return render(request, 'accounts/deal_form.html', {'form': form, 'title': 'Edit Deal', 'deal': deal})


@login_required(login_url='login')
def deal_delete(request, pk):
    deal = get_object_or_404(Deal, pk=pk)
    if request.method == 'POST':
        title = deal.title
        deal.delete()
        messages.success(request, f'Deal "{title}" deleted successfully.')
        return redirect('manage_deals')
    return render(request, 'accounts/confirm_delete.html', {'object_name': deal.title, 'type': 'Deal', 'cancel_url': 'manage_deals'})


# ==============================================================================
# REVIEWS MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_reviews(request):
    return redirect('manage_feedback')


@login_required(login_url='login')
def review_add(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Review added successfully!')
            return redirect('manage_reviews')
    else:
        form = ReviewForm()
    return render(request, 'accounts/review_form.html', {'form': form, 'title': 'Add New Customer Review'})


@login_required(login_url='login')
def review_edit(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, f'Review by "{review.customer_name}" updated successfully!')
            return redirect('manage_reviews')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'accounts/review_form.html', {'form': form, 'title': f'Edit Review by {review.customer_name}', 'review': review})


@login_required(login_url='login')
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        name = review.customer_name
        review.delete()
        messages.success(request, f'Review by "{name}" deleted successfully.')
        return redirect('manage_reviews')
    return render(request, 'accounts/confirm_delete.html', {'object_name': review.customer_name, 'type': 'Review', 'cancel_url': 'manage_reviews'})


@login_required(login_url='login')
def review_toggle(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = not review.is_approved
    review.save()
    status = "Approved" if review.is_approved else "Hidden"
    messages.success(request, f'Review by "{review.customer_name}" is now {status}.')
    return redirect('manage_reviews')


# ==============================================================================
# RESTAURANT SETTINGS MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_settings(request):
    return redirect('dashboard')


# ==============================================================================
# CUSTOMER FEEDBACK MANAGEMENT
# ==============================================================================
@login_required(login_url='login')
def manage_feedback(request):
    status_filter = request.GET.get('status', None)
    search_query = request.GET.get('q', '').strip()

    feedback_qs = CustomerFeedback.objects.all()

    if status_filter in ['all', 'pending', 'approved', 'rejected']:
        if status_filter != 'all':
            feedback_qs = feedback_qs.filter(status=status_filter)

    if search_query:
        feedback_qs = feedback_qs.filter(
            Q(customer_name__icontains=search_query) | Q(comment__icontains=search_query) | Q(email__icontains=search_query)
        )

    paginator = Paginator(feedback_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'feedback_list': page_obj,
        'current_status': status_filter,
        'search_query': search_query,
        'pending_count': CustomerFeedback.objects.filter(status='pending').count(),
        'approved_count': CustomerFeedback.objects.filter(status='approved').count(),
        'rejected_count': CustomerFeedback.objects.filter(status='rejected').count(),
        'all_count': CustomerFeedback.objects.count(),
    }
    return render(request, 'accounts/feedback.html', context)


@login_required(login_url='login')
def feedback_approve(request, pk):
    item = get_object_or_404(CustomerFeedback, pk=pk)
    item.status = 'approved'
    item.save()
    messages.success(request, f'Feedback from "{item.customer_name}" has been APPROVED and is now live on the website!')
    return redirect('manage_feedback')


@login_required(login_url='login')
def feedback_reject(request, pk):
    item = get_object_or_404(CustomerFeedback, pk=pk)
    item.status = 'rejected'
    item.save()
    messages.info(request, f'Feedback from "{item.customer_name}" has been REJECTED.')
    return redirect('manage_feedback')


@login_required(login_url='login')
def feedback_delete(request, pk):
    item = get_object_or_404(CustomerFeedback, pk=pk)
    if request.method == 'POST':
        name = item.customer_name
        item.delete()
        messages.success(request, f'Feedback from "{name}" has been deleted.')
        return redirect('manage_feedback')
    return render(request, 'accounts/confirm_delete.html', {'object_name': item.customer_name, 'type': 'Customer Feedback', 'cancel_url': 'manage_feedback'})


# ==============================================================================
# REAL-TIME ORDER NOTIFICATIONS API
# ==============================================================================
@login_required(login_url='login')
def api_get_notifications(request):
    unread_count = OrderNotification.objects.filter(is_read=False, order__isnull=False).count()
    notifications_qs = OrderNotification.objects.filter(order__isnull=False).select_related('order')[:20]

    today = timezone.now().date()
    orders_booked = Order.objects.filter(order_status='completed').count()
    today_orders_count = Order.objects.filter(created_at__date=today).count()
    income_aggregate = Order.objects.filter(order_status='completed', created_at__date=today).aggregate(total=Sum('total_price'))
    today_income = float(income_aggregate['total'] or 0)
    
    items = []
    now = timezone.now()
    for notif in notifications_qs:
        diff = now - notif.created_at
        seconds = int(diff.total_seconds())
        if seconds < 60:
            time_str = "Just now"
        elif seconds < 3600:
            mins = seconds // 60
            time_str = f"{mins}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            time_str = f"{hours}h ago"
        else:
            days = seconds // 86400
            time_str = f"{days}d ago"

        order_pk = notif.order.pk if notif.order else None
        order_url = reverse('order_detail', args=[order_pk]) if order_pk else '#'

        order_label = ''
        if notif.order:
            order_day_cnt = Order.objects.filter(created_at__date=notif.order.created_at.date(), created_at__lte=notif.order.created_at).count()
            order_label = f"Order #{order_day_cnt if order_day_cnt > 0 else notif.order.pk}"

        notif_title = notif.order.items_summary if (notif.order and notif.order.items_summary) else notif.title

        items.append({
            'id': notif.pk,
            'title': notif_title,
            'order_id': order_label,
            'customer_name': notif.customer_name,
            'total_price': float(notif.total_price),
            'notification_type': notif.notification_type,
            'is_read': notif.is_read,
            'time_ago': time_str,
            'order_url': order_url,
        })

    return JsonResponse({
        'status': 'success',
        'unread_count': unread_count,
        'notifications': items,
        'stats': {
            'orders_booked': orders_booked,
            'today_orders_count': today_orders_count,
            'today_income': today_income,
        }
    })


@login_required(login_url='login')
def api_mark_notification_read(request, pk):
    notif = get_object_or_404(OrderNotification, pk=pk)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
def api_mark_all_notifications_read(request):
    OrderNotification.objects.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
def api_delete_notification(request, pk):
    notif = get_object_or_404(OrderNotification, pk=pk)
    notif.delete()
    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
def analytics_visitors(request):
    data = get_visitor_analytics_data()
    return render(request, 'accounts/analytics_visitors.html', {'analytics': data})


@login_required(login_url='login')
def analytics_revenue(request):
    data = get_revenue_analytics_data()
    return render(request, 'accounts/analytics_revenue.html', {'analytics': data})


@login_required(login_url='login')
def export_visitors_csv(request):
    data = get_visitor_analytics_data()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="visitor_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['Metric Name', 'Visitor Count / Value'])
    writer.writerow(['Today', data['today']])
    writer.writerow(['This Week', data['this_week']])
    writer.writerow(['This Month', data['this_month']])
    writer.writerow(['This Year', data['this_year']])
    writer.writerow(['Busy Hours', data['busy_hours']])
    return response


@login_required(login_url='login')
def export_orders_csv(request):
    data = get_orders_analytics_data()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['Metric Category', 'Metric Name', 'Value'])
    writer.writerow(['Today', 'Orders Today', data['today']['orders_today']])
    writer.writerow(['Today', 'Pending Orders', data['today']['pending_orders']])
    writer.writerow(['Today', 'Completed Orders', data['today']['completed_orders']])
    writer.writerow(['Today', 'Cancelled Orders', data['today']['cancelled_orders']])
    writer.writerow(['Today', 'Peak Ordering Hour', data['today']['peak_ordering_hour']])
    writer.writerow(['Today', 'Average Order Value (PKR)', f"PKR {data['today']['avg_order_value']:.2f}"])
    writer.writerow([])
    writer.writerow(['This Week', 'Weekly Total Orders', data['week']['weekly_total_orders']])
    writer.writerow(['This Week', 'Busiest Day', data['week']['busiest_day']])
    writer.writerow(['Day Name', 'Date', 'Order Count'])
    for d in data['week']['days']:
        writer.writerow([d['day_name'], d['date'], d['count']])
    writer.writerow([])
    writer.writerow(['This Month', 'Current Month Orders', data['month']['current_month_orders']])
    writer.writerow(['This Month', 'Highest Month', data['month']['highest_month']])
    writer.writerow(['This Month', 'Average Monthly Orders', f"{data['month']['avg_orders_per_month']:.1f}"])
    writer.writerow(['Month Name', 'Order Count'])
    for m in data['month']['months']:
        writer.writerow([m['month_name'], m['count']])
    writer.writerow([])
    writer.writerow(['Top Selling Product Rank', 'Product Name', 'Total Items Sold'])
    for p in data['top_selling_products']:
        writer.writerow([p['rank'], p['name'], p['orders_count']])
    return response


@login_required(login_url='login')
def export_revenue_csv(request):
    data = get_revenue_analytics_data()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="revenue_analytics.csv"'
    writer = csv.writer(response)
    writer.writerow(['Metric Category', 'Metric Name', 'Value'])
    writer.writerow(['Today', 'Today Revenue (PKR)', f"PKR {data['today']['today_revenue']:.2f}"])
    writer.writerow(['Today', 'Average Order Value (PKR)', f"PKR {data['today']['avg_order_value']:.2f}"])
    writer.writerow(['Today', 'Highest Single Order (PKR)', f"PKR {data['today']['highest_order']:.2f}"])
    writer.writerow(['Today', 'Lowest Single Order (PKR)', f"PKR {data['today']['lowest_order']:.2f}"])
    writer.writerow([])
    writer.writerow(['This Week', 'Weekly Total Revenue (PKR)', f"PKR {data['week']['weekly_total_revenue']:.2f}"])
    writer.writerow(['This Week', 'Highest Revenue Day', data['week']['highest_revenue_day']])
    writer.writerow(['Day Name', 'Date', 'Revenue (PKR)'])
    for d in data['week']['days']:
        writer.writerow([d['day_name'], d['date'], f"PKR {d['revenue']:.2f}"])
    writer.writerow([])
    writer.writerow(['This Month', 'Current Month Revenue (PKR)', f"PKR {data['month']['current_month_revenue']:.2f}"])
    writer.writerow(['This Month', 'Highest Revenue Month', data['month']['highest_revenue_month']])
    writer.writerow(['This Month', 'Average Monthly Revenue (PKR)', f"PKR {data['month']['avg_monthly_revenue']:.2f}"])
    writer.writerow(['Month Name', 'Revenue (PKR)'])
    for m in data['month']['months']:
        writer.writerow([m['month_name'], f"PKR {m['revenue']:.2f}"])
    return response





@login_required(login_url='login')
def analytics_visitors_today(request):
    data = get_visitor_analytics_data()
    return render(request, 'accounts/analytics_visitors_today.html', {'analytics': data})


@login_required(login_url='login')
def analytics_visitors_week(request):
    data = get_visitor_analytics_data()
    return render(request, 'accounts/analytics_visitors_week.html', {'analytics': data})


@login_required(login_url='login')
def analytics_visitors_month(request):
    data = get_visitor_analytics_data()
    return render(request, 'accounts/analytics_visitors_month.html', {'analytics': data})


@login_required(login_url='login')
def analytics_visitors_year(request):
    data = get_visitor_analytics_data()
    return render(request, 'accounts/analytics_visitors_year.html', {'analytics': data})


@login_required(login_url='login')
def analytics_revenue(request):
    data = get_revenue_analytics_data()
    return render(request, 'accounts/analytics_revenue.html', {'analytics': data})


@login_required(login_url='login')
def analytics_revenue_today(request):
    data = get_revenue_analytics_data()
    return render(request, 'accounts/analytics_revenue_today.html', {'analytics': data})


@login_required(login_url='login')
def analytics_revenue_week(request):
    data = get_revenue_analytics_data()
    return render(request, 'accounts/analytics_revenue_week.html', {'analytics': data})


@login_required(login_url='login')
def analytics_revenue_month(request):
    data = get_revenue_analytics_data()
    return render(request, 'accounts/analytics_revenue_month.html', {'analytics': data})


@login_required(login_url='login')
def analytics_revenue_year(request):
    data = get_revenue_analytics_data()
    return render(request, 'accounts/analytics_revenue_year.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders_today(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders_today.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders_week(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders_week.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders_month(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders_month.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders_year(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders_year.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders_today_pending(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders_today_pending.html', {'analytics': data})


@login_required(login_url='login')
def analytics_orders_today_completed(request):
    data = get_orders_analytics_data()
    return render(request, 'accounts/analytics_orders_today_completed.html', {'analytics': data})
