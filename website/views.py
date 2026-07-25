import json
import random
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from .models import RestaurantInfo, Category, Product, Deal, Review, CustomerFeedback, Order, OrderItem, DailyVisit, OrderNotification
from .forms import CustomerFeedbackForm

def track_visit(request):
    try:
        today = timezone.now().date()
        visit, _ = DailyVisit.objects.get_or_create(date=today)
        DailyVisit.objects.filter(pk=visit.pk).update(count=F('count') + 1)
    except Exception:
        pass

def index(request):
    track_visit(request)
    deals = Deal.objects.filter(is_active=True)
    # Combine static approved reviews and approved customer feedback
    curated_reviews = list(Review.objects.filter(is_approved=True))
    approved_feedback = CustomerFeedback.objects.filter(status='approved')
    
    # Map customer feedback items to review display format
    feedback_reviews = [
        {
            'customer_name': fb.customer_name,
            'reviewer_role': 'Verified Diner',
            'rating': fb.rating,
            'comment': f'"{fb.comment}"' if not fb.comment.startswith('"') else fb.comment,
            'avatar_url': fb.avatar_file.url if fb.avatar_file else f'https://i.pravatar.cc/120?img={(fb.id * 7) % 70 + 1}'
        }
        for fb in approved_feedback
    ]
    
    combined_reviews = curated_reviews + feedback_reviews

    return render(request, 'website/index.html', {
        'deals': deals,
        'reviews': combined_reviews,
    })

from django.core.paginator import Paginator
from django.templatetags.static import static

PER_PAGE = 9

def menu(request):
    categories = Category.objects.filter(is_active=True)
    products_qs = Product.objects.filter(category__is_active=True).select_related('category')
    paginator = Paginator(products_qs, PER_PAGE)
    first_page = paginator.get_page(1)
    deals = Deal.objects.filter(is_active=True)
    
    return render(request, 'website/menu.html', {
        'categories': categories,
        'products': first_page.object_list,
        'has_more': first_page.has_next(),
        'total_count': paginator.count,
        'deals': deals,
    })

def api_products(request):
    cat_slug = request.GET.get('category', 'all')
    search_q = request.GET.get('search', '').strip()
    page_num = request.GET.get('page', 1)
    
    try:
        page_num = int(page_num)
    except (ValueError, TypeError):
        page_num = 1
        
    qs = Product.objects.filter(category__is_active=True).select_related('category')
    
    if cat_slug and cat_slug != 'all' and cat_slug != 'deals':
        qs = qs.filter(category__slug=cat_slug)
        
    if search_q:
        from django.db.models import Q
        qs = qs.filter(Q(name__icontains=search_q) | Q(description__icontains=search_q))
        
    paginator = Paginator(qs, PER_PAGE)
    page_obj = paginator.get_page(page_num)
    
    items_data = []
    for prod in page_obj.object_list:
        img_url = prod.image_file.url if prod.image_file else static(prod.image)
        items_data.append({
            'item_code': prod.item_code,
            'name': prod.name,
            'price': int(round(prod.price)),
            'description': prod.description or '',
            'image_url': img_url,
            'category_slug': prod.category.slug,
            'is_available': prod.is_available,
            'custom_style': prod.custom_style or '',
        })
        
    return JsonResponse({
        'products': items_data,
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count,
    })

def about(request):
    return render(request, 'website/about.html')

def privacy(request):
    return render(request, 'website/privacy.html')

def terms(request):
    return render(request, 'website/terms.html')

def contact(request):
    if request.method == 'POST':
        form = CustomerFeedbackForm(request.POST, request.FILES)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.status = 'pending'
            feedback.save()
            messages.success(request, 'Thank you! Your feedback has been received and is currently pending review by our team.')
            return redirect('contact')
    else:
        form = CustomerFeedbackForm()

    return render(request, 'website/contact.html', {'feedback_form': form})


@csrf_exempt
def api_create_order(request):
    if request.method == 'POST':
        try:
            info = RestaurantInfo.objects.first()
            if info and not info.is_open:
                return JsonResponse({'status': 'error', 'message': 'Ordering is currently unavailable because the restaurant is closed. Please visit again during our opening hours.'}, status=403)

            data = json.loads(request.body)
            customer_name = data.get('customer_name', '').strip()
            customer_phone = data.get('customer_phone', '').strip()
            delivery_address = data.get('delivery_address', '').strip()
            order_notes = data.get('order_notes', '').strip()
            cart_items = data.get('cart_items', [])

            if not customer_name or not customer_phone or not delivery_address:
                return JsonResponse({'status': 'error', 'message': 'Customer Name, Phone Number, and Delivery Address are required.'}, status=400)

            if not cart_items:
                return JsonResponse({'status': 'error', 'message': 'Cart is empty.'}, status=400)

            # Generate unique order_id: e.g. DFS-20260723-8492
            today_str = timezone.now().strftime('%Y%m%d')
            rand_num = random.randint(1000, 9999)
            order_id = f"DFS-{today_str}-{rand_num}"

            # Validate stock availability for all cart items first
            for item_data in cart_items:
                item_code = item_data.get('id', '')
                product_obj = Product.objects.filter(item_code=item_code).first()
                if product_obj and not product_obj.is_available:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'"{product_obj.name}" is currently out of stock. Please remove it from your cart before checkout.'
                    }, status=400)

            total_price = 0
            order = Order.objects.create(
                order_id=order_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                delivery_address=delivery_address,
                order_notes=order_notes,
                total_price=0,
                order_status='pending',
                payment_status='unpaid',
            )

            for item_data in cart_items:
                name = item_data.get('name', 'Item')
                item_code = item_data.get('id', '')
                qty = int(item_data.get('quantity', 1))
                price = float(item_data.get('price', 0))
                subtotal = price * qty
                total_price += subtotal

                # Try matching product
                product_obj = Product.objects.filter(item_code=item_code).first()

                OrderItem.objects.create(
                    order=order,
                    product=product_obj,
                    product_name=name,
                    quantity=qty,
                    unit_price=price,
                    subtotal=subtotal
                )

            order.total_price = total_price
            order.save()

            # Create Real-Time Order Notification
            OrderNotification.objects.create(
                order=order,
                title=order.items_summary or "New Order",
                message=f"Received order from {order.customer_name} for Rs. {total_price:.0f}",
                customer_name=order.customer_name,
                total_price=total_price,
                notification_type='new_order',
                is_read=False
            )

            return JsonResponse({
                'status': 'success',
                'order_id': order.order_id,
                'total_price': total_price,
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
