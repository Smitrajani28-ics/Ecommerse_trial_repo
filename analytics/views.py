from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, OrderItem
from products.models import Product
from django.contrib.auth.models import User
from reviews.models import Review


@staff_member_required
def dashboard(request):
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)

    paid_orders = Order.objects.filter(payment_status='paid')
    recent_orders = paid_orders.filter(created_at__gte=last_30_days)

    # Summary stats
    stats = {
        'total_revenue': paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0,
        'monthly_revenue': recent_orders.aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_orders': paid_orders.count(),
        'monthly_orders': recent_orders.count(),
        'total_customers': User.objects.filter(is_active=True, is_staff=False).count(),
        'new_customers': User.objects.filter(date_joined__gte=last_30_days, is_staff=False).count(),
        'avg_order_value': paid_orders.aggregate(avg=Avg('total_amount'))['avg'] or 0,
    }

    # Daily sales (last 30 days)
    daily_sales = (
        recent_orders
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('date')
    )

    # Top 10 products by revenue
    top_products = (
        OrderItem.objects.filter(order__payment_status='paid')
        .values('product__name')
        .annotate(total_revenue=Sum('total_price'), total_sold=Sum('quantity'))
        .order_by('-total_revenue')[:10]
    )

    # Recent orders
    latest_orders = Order.objects.select_related('user').order_by('-created_at')[:10]

    # Low stock products
    low_stock = Product.objects.filter(is_active=True, stock_quantity__lte=5).order_by('stock_quantity')[:10]

    # Monthly revenue (last 6 months)
    six_months_ago = now - timedelta(days=180)
    monthly_revenue = (
        paid_orders.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('total_amount'), count=Count('id'))
        .order_by('month')
    )

    # Order status breakdown
    status_breakdown = (
        Order.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return render(request, 'analytics/dashboard.html', {
        'stats': stats,
        'daily_sales': list(daily_sales),
        'top_products': top_products,
        'latest_orders': latest_orders,
        'low_stock': low_stock,
        'monthly_revenue': list(monthly_revenue),
        'status_breakdown': status_breakdown,
    })
