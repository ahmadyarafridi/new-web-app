import csv
from datetime import timedelta
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Max, Min, Q
from django.db.models.functions import ExtractHour
from website.models import Order, OrderItem, DailyVisit, Product, Category


def get_visitor_analytics_data():
    now = timezone.localtime(timezone.now())
    today = now.date()  # Real-time live date
    year = today.year
    month = today.month

    # 1. Today
    today_visit = DailyVisit.objects.filter(date=today).first()
    today_visitors = today_visit.count if today_visit else 0

    # 2. This Week (Monday to Sunday)
    start_of_week = today - timedelta(days=today.weekday())
    week_days = []
    weekly_total = 0
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_name = day_date.strftime('%A')
        visit_obj = DailyVisit.objects.filter(date=day_date).first()
        cnt = visit_obj.count if visit_obj else 0
        week_days.append({
            'name': day_name,
            'date': day_date.strftime('%b %d'),
            'count': cnt
        })
        weekly_total += cnt

    # 3. This Month (4 Weeks of current month)
    start_of_month = today.replace(day=1)
    month_weeks = []
    monthly_total = 0
    for w in range(4):
        w_start = start_of_month + timedelta(days=w * 7)
        w_end = w_start + timedelta(days=6)
        w_cnt = sum(DailyVisit.objects.filter(date__range=[w_start, w_end]).values_list('count', flat=True))
        month_weeks.append({
            'name': f"Week {w + 1}",
            'range': f"{w_start.strftime('%b %d')} – {w_end.strftime('%b %d')}",
            'count': w_cnt
        })
        monthly_total += w_cnt

    # 4. This Year (January to December of current year)
    year_months = []
    yearly_total = 0
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]

    for m_idx in range(1, 13):
        m_name = month_names[m_idx - 1]
        m_cnt = sum(DailyVisit.objects.filter(date__year=year, date__month=m_idx).values_list('count', flat=True))
        year_months.append({
            'name': m_name,
            'year': year,
            'count': m_cnt,
            'is_current': (m_idx == month)
        })
        yearly_total += m_cnt

    # 5. Today Hourly Breakdown (11:00 AM to 11:00 PM)
    today_hours = []
    for h in range(11, 23):
        start_period = "AM" if h < 12 else "PM"
        h12 = h if (h <= 12 and h > 0) else (h - 12 if h > 12 else 12)
        next_h = (h + 1) % 24
        end_period = "AM" if next_h < 12 else "PM"
        next_h12 = next_h if (next_h <= 12 and next_h > 0) else (next_h - 12 if next_h > 12 else 12)
        slot_label = f"{h12:02d}:00 {start_period} – {next_h12:02d}:00 {end_period}"
        today_hours.append({
            'label': slot_label,
            'count': 0
        })

    return {
        'today': today_visitors,
        'this_week': weekly_total,
        'this_month': monthly_total,
        'this_year': yearly_total,
        'today_hours': today_hours,
        'week_rows': week_days,
        'month_rows': month_weeks,
        'year_rows': year_months,
    }


def get_orders_analytics_data():
    now = timezone.localtime(timezone.now())
    today = now.date()
    year = today.year
    month = today.month

    # 1. Today
    today_orders = Order.objects.filter(Q(created_at__date=today) | Q(updated_at__date=today))
    today_orders_qs = today_orders.order_by('-created_at')
    today_pending_qs = Order.objects.filter(order_status='pending', created_at__date=today).order_by('-created_at')
    today_completed_qs = Order.objects.filter(order_status='completed').filter(Q(created_at__date=today) | Q(updated_at__date=today)).order_by('-updated_at')
    orders_today_count = today_orders.count()
    today_pending_count = today_pending_qs.count()
    today_completed_count = today_completed_qs.count()

    # 2. This Week (Monday to Sunday - Completed Orders)
    start_of_week = today - timedelta(days=today.weekday())
    week_days = []
    weekly_total = 0
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_name = day_date.strftime('%A')
        cnt = Order.objects.filter(order_status='completed').filter(Q(created_at__date=day_date) | Q(updated_at__date=day_date)).count()
        week_days.append({
            'name': day_name,
            'date': day_date.strftime('%b %d'),
            'count': cnt
        })
        weekly_total += cnt

    # 3. This Month (4 Weeks of current month - Completed Orders)
    start_of_month = today.replace(day=1)
    month_weeks = []
    monthly_total = 0
    for w in range(4):
        w_start = start_of_month + timedelta(days=w * 7)
        w_end = w_start + timedelta(days=6)
        w_cnt = Order.objects.filter(order_status='completed').filter(Q(created_at__date__range=[w_start, w_end]) | Q(updated_at__date__range=[w_start, w_end])).count()
        month_weeks.append({
            'name': f"Week {w + 1}",
            'range': f"{w_start.strftime('%b %d')} – {w_end.strftime('%b %d')}",
            'count': w_cnt
        })
        monthly_total += w_cnt

    # 4. This Year (January to December of current year - Completed Orders)
    year_months = []
    yearly_total = 0
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]

    for m_idx in range(1, 13):
        m_name = month_names[m_idx - 1]
        m_cnt = Order.objects.filter(order_status='completed').filter(Q(created_at__year=year, created_at__month=m_idx) | Q(updated_at__year=year, updated_at__month=m_idx)).count()
        year_months.append({
            'name': m_name,
            'year': year,
            'count': m_cnt,
            'is_current': (m_idx == month)
        })
        yearly_total += m_cnt

    # 5. Today Hourly Breakdown (11:00 AM to 11:00 PM)
    today_hours = []
    for h in range(11, 23):
        start_period = "AM" if h < 12 else "PM"
        h12 = h if (h <= 12 and h > 0) else (h - 12 if h > 12 else 12)
        next_h = (h + 1) % 24
        end_period = "AM" if next_h < 12 else "PM"
        next_h12 = next_h if (next_h <= 12 and next_h > 0) else (next_h - 12 if next_h > 12 else 12)
        slot_label = f"{h12:02d}:00 {start_period} – {next_h12:02d}:00 {end_period}"

        cnt = today_orders.filter(order_status='completed', created_at__hour=h).count()
        today_hours.append({
            'label': slot_label,
            'count': cnt
        })

    return {
        'today': orders_today_count,
        'today_pending_count': today_pending_count,
        'today_completed_count': today_completed_count,
        'this_week': weekly_total,
        'this_month': monthly_total,
        'this_year': yearly_total,
        'today_orders_list': today_orders_qs,
        'today_pending_list': today_pending_qs,
        'today_completed_list': today_completed_qs,
        'today_hours': today_hours,
        'week_rows': week_days,
        'month_rows': month_weeks,
        'year_rows': year_months,
    }


def get_revenue_analytics_data():
    now = timezone.localtime(timezone.now())
    today = now.date()
    year = today.year
    month = today.month

    # 1. Today (Completed Orders Revenue)
    today_completed_orders = Order.objects.filter(order_status='completed').filter(Q(created_at__date=today) | Q(updated_at__date=today)).order_by('-updated_at')
    today_revenue = float(today_completed_orders.aggregate(tot=Sum('total_price'))['tot'] or 0)

    # 2. This Week (Monday to Sunday)
    start_of_week = today - timedelta(days=today.weekday())
    week_days = []
    weekly_total = 0
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        day_name = day_date.strftime('%A')
        rev = float(Order.objects.filter(order_status='completed').filter(Q(created_at__date=day_date) | Q(updated_at__date=day_date)).aggregate(tot=Sum('total_price'))['tot'] or 0)
        week_days.append({
            'name': day_name,
            'date': day_date.strftime('%b %d'),
            'revenue': rev
        })
        weekly_total += rev

    # 3. This Month (4 Weeks of current month)
    start_of_month = today.replace(day=1)
    month_weeks = []
    monthly_total = 0
    for w in range(4):
        w_start = start_of_month + timedelta(days=w * 7)
        w_end = w_start + timedelta(days=6)
        w_rev = float(Order.objects.filter(order_status='completed').filter(Q(created_at__date__range=[w_start, w_end]) | Q(updated_at__date__range=[w_start, w_end])).aggregate(tot=Sum('total_price'))['tot'] or 0)
        month_weeks.append({
            'name': f"Week {w + 1}",
            'range': f"{w_start.strftime('%b %d')} – {w_end.strftime('%b %d')}",
            'revenue': w_rev
        })
        monthly_total += w_rev

    # 4. This Year (January to December of current year)
    year_months = []
    yearly_total = 0
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]

    for m_idx in range(1, 13):
        m_name = month_names[m_idx - 1]
        m_rev = float(Order.objects.filter(order_status='completed').filter(Q(created_at__year=year, created_at__month=m_idx) | Q(updated_at__year=year, updated_at__month=m_idx)).aggregate(tot=Sum('total_price'))['tot'] or 0)
        year_months.append({
            'name': m_name,
            'year': year,
            'revenue': m_rev,
            'is_current': (m_idx == month)
        })
        yearly_total += m_rev

    # 5. Today Hourly Breakdown (11:00 AM to 11:00 PM)
    today_hours = []
    for h in range(11, 23):
        start_period = "AM" if h < 12 else "PM"
        h12 = h if (h <= 12 and h > 0) else (h - 12 if h > 12 else 12)
        next_h = (h + 1) % 24
        end_period = "AM" if next_h < 12 else "PM"
        next_h12 = next_h if (next_h <= 12 and next_h > 0) else (next_h - 12 if next_h > 12 else 12)
        slot_label = f"{h12:02d}:00 {start_period} – {next_h12:02d}:00 {end_period}"

        h_rev = float(today_completed_orders.filter(created_at__hour=h).aggregate(tot=Sum('total_price'))['tot'] or 0)
        today_hours.append({
            'label': slot_label,
            'revenue': h_rev
        })

    return {
        'today': today_revenue,
        'today_completed_list': today_completed_orders,
        'this_week': weekly_total,
        'this_month': monthly_total,
        'this_year': yearly_total,
        'today_hours': today_hours,
        'week_rows': week_days,
        'month_rows': month_weeks,
        'year_rows': year_months,
    }


def get_product_analytics_data(sort_by='most_sold'):
    total_products = Product.objects.count()
    in_stock_products = Product.objects.filter(is_available=True).count()
    out_of_stock_products = Product.objects.filter(is_available=False).count()
    total_categories = Category.objects.count()

    all_products_qs = Product.objects.select_related('category').annotate(
        times_ordered=Sum('order_items__quantity'),
        total_revenue=Sum('order_items__subtotal')
    )

    products_list = []
    for p in all_products_qs:
        qty = p.times_ordered or 0
        rev = float(p.total_revenue or 0)
        img_url = p.image_file.url if p.image_file else (p.image if p.image else '/static/images/menu-placeholder.jpg')
        products_list.append({
            'id': p.pk,
            'name': p.name,
            'category_name': p.category.name if p.category else 'Uncategorized',
            'is_available': p.is_available,
            'status_label': 'In Stock' if p.is_available else 'Out of Stock',
            'image_url': img_url,
            'times_ordered': qty,
            'total_revenue': rev,
        })

    # Top 10 Best-Selling
    top_10 = sorted(products_list, key=lambda x: x['times_ordered'], reverse=True)[:10]
    for idx, item in enumerate(top_10):
        if idx == 0:
            item['badge'] = '🥇'
            item['badge_class'] = 'gold'
        elif idx == 1:
            item['badge'] = '🥈'
            item['badge_class'] = 'silver'
        elif idx == 2:
            item['badge'] = '🥉'
            item['badge_class'] = 'bronze'
        else:
            item['badge'] = f"#{idx+1}"
            item['badge_class'] = 'standard'

    # Low Selling (Bottom 10 by times_ordered)
    low_10 = sorted(products_list, key=lambda x: x['times_ordered'])[:10]

    # Full table sorting
    if sort_by == 'least_sold':
        sorted_full = sorted(products_list, key=lambda x: x['times_ordered'])
    else:  # most_sold (default)
        sorted_full = sorted(products_list, key=lambda x: x['times_ordered'], reverse=True)

    # Most sold product (top 1)
    most_sold = sorted(products_list, key=lambda x: x['times_ordered'], reverse=True)
    most_sold_product = most_sold[0] if most_sold else None

    # Least sold product (bottom 1 — only those actually ordered)
    least_sold = sorted([p for p in products_list if p['times_ordered'] > 0], key=lambda x: x['times_ordered'])
    if not least_sold:
        least_sold = sorted(products_list, key=lambda x: x['times_ordered'])
    least_sold_product = least_sold[0] if least_sold else None

    return {
        'summary': {
            'total_products': total_products,
            'in_stock': in_stock_products,
            'out_of_stock': out_of_stock_products,
            'total_categories': total_categories,
        },
        'top_10': top_10,
        'low_10': low_10,
        'all_products': sorted_full,
        'current_sort': sort_by,
        'most_sold_product': most_sold_product,
        'least_sold_product': least_sold_product,
    }
