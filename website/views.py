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

from django.db import OperationalError, ProgrammingError
from django.core.management import call_command

def ensure_db_ready():
    try:
        call_command('migrate', interactive=False)
        call_command('seed_data')
    except Exception as e:
        print("ensure_db_ready error:", e)

def track_visit(request):
    try:
        today = timezone.now().date()
        visit, _ = DailyVisit.objects.get_or_create(date=today)
        DailyVisit.objects.filter(pk=visit.pk).update(count=F('count') + 1)
    except Exception:
        pass

from django.core.paginator import Paginator
from django.templatetags.static import static

PER_PAGE = 9

def index(request):
    track_visit(request)
    try:
        categories = list(Category.objects.filter(is_active=True))
        products_qs = Product.objects.filter(category__is_active=True).select_related('category').order_by('-id')
        paginator = Paginator(products_qs, PER_PAGE)
        first_page = paginator.get_page(1)
        deals = list(Deal.objects.filter(is_active=True).order_by('-id'))
        approved_feedback = list(CustomerFeedback.objects.filter(status='approved').order_by('-created_at', '-id'))
        curated_reviews = list(Review.objects.filter(is_approved=True).order_by('display_order', '-id'))

        seen_names = set()
        all_approved = []
        for fb in approved_feedback:
            if fb.customer_name not in seen_names:
                all_approved.append({
                    'customer_name': fb.customer_name,
                    'reviewer_role': 'Verified Diner',
                    'rating': fb.rating,
                    'comment': fb.comment,
                    'avatar_url': fb.avatar_src
                })
                seen_names.add(fb.customer_name)

        for rev in curated_reviews:
            if rev.customer_name not in seen_names:
                all_approved.append({
                    'customer_name': rev.customer_name,
                    'reviewer_role': getattr(rev, 'reviewer_role', None) or 'Food Enthusiast',
                    'rating': rev.rating,
                    'comment': rev.comment,
                    'avatar_url': rev.avatar_file.url if rev.avatar_file else (rev.avatar_url or 'https://i.pravatar.cc/120?img=68')
                })
                seen_names.add(rev.customer_name)
        all_products = list(products_qs)
    except (OperationalError, ProgrammingError):
        ensure_db_ready()
        categories = list(Category.objects.filter(is_active=True))
        products_qs = Product.objects.filter(category__is_active=True).select_related('category').order_by('-id')
        all_products = list(products_qs)
        paginator = Paginator(products_qs, PER_PAGE)
        first_page = paginator.get_page(1)
        deals = list(Deal.objects.filter(is_active=True).order_by('-id'))
        approved_feedback = list(CustomerFeedback.objects.filter(status='approved').order_by('-created_at', '-id'))
        curated_reviews = list(Review.objects.filter(is_approved=True).order_by('display_order', '-id'))
        seen_names = set()
        all_approved = []
        for fb in approved_feedback:
            if fb.customer_name not in seen_names:
                all_approved.append({
                    'customer_name': fb.customer_name,
                    'reviewer_role': 'Verified Diner',
                    'rating': fb.rating,
                    'comment': fb.comment,
                    'avatar_url': fb.avatar_src
                })
                seen_names.add(fb.customer_name)
        for rev in curated_reviews:
            if rev.customer_name not in seen_names:
                all_approved.append({
                    'customer_name': rev.customer_name,
                    'reviewer_role': getattr(rev, 'reviewer_role', None) or 'Food Enthusiast',
                    'rating': rev.rating,
                    'comment': rev.comment,
                    'avatar_url': rev.avatar_file.url if rev.avatar_file else (rev.avatar_url or 'https://i.pravatar.cc/120?img=68')
                })
                seen_names.add(rev.customer_name)

    return render(request, 'website/index.html', {
        'categories': categories,
        'products': first_page.object_list,
        'all_products': all_products,
        'has_more': first_page.has_next(),
        'total_count': paginator.count,
        'deals': deals,
        'reviews': all_approved,
    })

def menu(request):
    return redirect('/#menu')

def api_products(request):
    cat_slug = request.GET.get('category', 'all')
    search_q = request.GET.get('search', '').strip()
    page_num = request.GET.get('page', 1)
    
    try:
        page_num = int(page_num)
    except (ValueError, TypeError):
        page_num = 1

    if cat_slug == 'deals':
        deals_qs = Deal.objects.filter(is_active=True).order_by('-id')
        if search_q:
            from django.db.models import Q
            deals_qs = deals_qs.filter(Q(title__icontains=search_q) | Q(description__icontains=search_q))
        items_data = []
        for deal in deals_qs:
            img_url = deal.image_file.url if deal.image_file else static(deal.image)
            items_data.append({
                'item_code': deal.item_code,
                'name': deal.title,
                'price': int(round(deal.price)),
                'description': deal.description or '',
                'image_url': img_url,
                'category_slug': 'deals',
                'is_available': True,
                'custom_style': '',
            })
        return JsonResponse({
            'products': items_data,
            'has_next': False,
            'current_page': 1,
            'total_pages': 1,
            'total_count': len(items_data),
        })

    qs = Product.objects.filter(category__is_active=True).select_related('category').order_by('-id')
    
    if cat_slug and cat_slug != 'all':
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

def legal_document(request, doc_type):
    info = RestaurantInfo.objects.first()
    rest_name = info.name if info else "Amazing Foods"
    rest_email = info.email if info else "info@amazingfoods.pk"
    rest_phone = info.phone if info else "+92 323 2870355"

    if doc_type == 'privacy':
        context = {
            'page_title': 'Privacy Policy',
            'section_tag': 'Privacy & Data Security',
            'updated_date': 'July 2026',
            'legal_items': [
                {
                    'title': '1. Information We Collect',
                    'content': f'When you place a WhatsApp pre-order on {rest_name}, we collect your full name, phone number, delivery address, and order notes to fulfill your food order.'
                },
                {
                    'title': '2. How We Use Your Information',
                    'content': 'Your details are used strictly to prepare your meal, process food delivery, and communicate order updates via WhatsApp. We never sell, rent, or trade your personal information with third-party advertisers.'
                },
                {
                    'title': '3. Cookies & Local Storage',
                    'content': 'We use standard browser LocalStorage solely to keep track of your active shopping cart items while browsing our menu. No tracking cookies are used to monitor external web activity.'
                },
                {
                    'title': '4. Contact Us',
                    'content': f'If you have any questions regarding your personal privacy, feel free to reach out to us at {rest_email} or via phone at {rest_phone}.'
                },
            ]
        }
    else:
        context = {
            'page_title': 'Terms of Service',
            'section_tag': 'Legal Information',
            'updated_date': 'July 2026',
            'legal_items': [
                {
                    'title': '1. Order Placement & WhatsApp Confirmation',
                    'content': f'All online pre-orders placed through {rest_name} are transmitted via WhatsApp for final kitchen confirmation. Your order is officially accepted once our team confirms your order details and delivery address on WhatsApp.'
                },
                {
                    'title': '2. Pricing & Currency',
                    'content': 'All prices listed on our menu are in Pakistani Rupees (PKR / Rs.) and include applicable local service taxes. We reserve the right to modify menu prices or daily deal promotions without prior notice.'
                },
                {
                    'title': '3. Operating Hours & Stock Availability',
                    'content': 'Our online pre-ordering operates during active kitchen hours (Lunch: 11:00 AM – 4:00 PM | Dinner: 5:00 PM – 11:00 PM). Item availability is subject to daily fresh ingredients. If an ordered item is out of stock, our team will offer a substitute or adjustment on WhatsApp.'
                },
                {
                    'title': '4. Order Cancellation',
                    'content': f'Orders can be canceled free of charge before food preparation begins by contacting our kitchen on WhatsApp at {rest_phone}. Once cooking has started, cancellations cannot be processed.'
                },
                {
                    'title': '5. Dietary Allergies & Special Instructions',
                    'content': 'Customers are responsible for specifying any severe food allergies (nuts, dairy, gluten, spices) in the special order notes when submitting their pre-order.'
                },
            ]
        }
    return render(request, 'website/legal.html', context)

def privacy(request):
    return legal_document(request, 'privacy')

def terms(request):
    return legal_document(request, 'terms')

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
