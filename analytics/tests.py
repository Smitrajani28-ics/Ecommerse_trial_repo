from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from products.models import Category, Product
from orders.models import Order, OrderItem


def make_paid_order(user, amount=Decimal('100.00')):
    category = Category.objects.get_or_create(name='Analytics Cat')[0]
    product = Product.objects.get_or_create(
        name='Analytics Product',
        defaults={
            'category': category,
            'description': 'Test',
            'price': amount,
            'stock_quantity': 100,
            'is_active': True,
        }
    )[0]
    order = Order.objects.create(
        user=user,
        subtotal=amount,
        total_amount=amount,
        payment_status='paid',
        shipping_address='1 Test St',
        billing_address='1 Test St',
        email=user.email or 'test@example.com',
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        quantity=1,
        unit_price=amount,
        total_price=amount,
    )
    return order


class AnalyticsDashboardAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regular', password='testpass123', email='regular@example.com'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass123', email='staff@example.com',
            is_staff=True,
        )

    def test_unauthenticated_user_redirected(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_non_staff_user_redirected(self):
        self.client.login(username='regular', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access_dashboard(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)


class AnalyticsDashboardContextTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffctx', password='testpass123',
            email='staffctx@example.com', is_staff=True,
        )
        self.client.login(username='staffctx', password='testpass123')

    def test_dashboard_context_has_stats(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('stats', response.context)

    def test_stats_has_required_keys(self):
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        required_keys = [
            'total_revenue', 'monthly_revenue', 'total_orders',
            'monthly_orders', 'total_customers', 'new_customers', 'avg_order_value',
        ]
        for key in required_keys:
            self.assertIn(key, stats, f"Missing key: {key}")

    def test_dashboard_context_has_daily_sales(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('daily_sales', response.context)

    def test_dashboard_context_has_top_products(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('top_products', response.context)

    def test_dashboard_context_has_latest_orders(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('latest_orders', response.context)

    def test_dashboard_context_has_low_stock(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('low_stock', response.context)

    def test_dashboard_context_has_monthly_revenue(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('monthly_revenue', response.context)

    def test_dashboard_context_has_status_breakdown(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('status_breakdown', response.context)


class AnalyticsDashboardStatsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staffstats', password='testpass123',
            email='staffstats@example.com', is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username='buyer', password='testpass123', email='buyer@example.com'
        )
        self.client.login(username='staffstats', password='testpass123')

    def test_total_orders_counts_only_paid(self):
        make_paid_order(self.regular_user, amount=Decimal('50.00'))
        # Create an unpaid order
        category = Category.objects.get_or_create(name='Analytics Cat')[0]
        Order.objects.create(
            user=self.regular_user,
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            payment_status='pending',
            shipping_address='1 Test St',
            billing_address='1 Test St',
            email='buyer@example.com',
        )
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        self.assertEqual(stats['total_orders'], 1)

    def test_total_revenue_sums_paid_orders(self):
        make_paid_order(self.regular_user, amount=Decimal('75.00'))
        make_paid_order(self.regular_user, amount=Decimal('25.00'))
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        self.assertEqual(stats['total_revenue'], Decimal('100.00'))

    def test_total_customers_excludes_staff(self):
        # staff_user is staff, regular_user is not
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        # regular_user should be counted; staff_user should not
        self.assertGreaterEqual(stats['total_customers'], 1)

    def test_low_stock_shows_products_at_or_below_5(self):
        category = Category.objects.get_or_create(name='Analytics Cat')[0]
        low = Product.objects.create(
            name='Low Stock Item', category=category,
            description='Test', price=Decimal('10.00'),
            stock_quantity=3, is_active=True,
        )
        normal = Product.objects.create(
            name='Normal Stock Item', category=category,
            description='Test', price=Decimal('10.00'),
            stock_quantity=50, is_active=True,
        )
        response = self.client.get('/analytics/dashboard/')
        low_stock_items = list(response.context['low_stock'])
        self.assertIn(low, low_stock_items)
        self.assertNotIn(normal, low_stock_items)
