from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from products.models import Category, Product
from orders.models import Order, OrderItem


class AnalyticsDashboardAccessTest(TestCase):
    """Tests for the @staff_member_required analytics dashboard view."""

    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regularuser', password='testpass123',
        )
        self.staff_user = User.objects.create_user(
            username='staffuser', password='testpass123',
            is_staff=True,
        )

    def test_dashboard_redirects_anonymous_user(self):
        response = self.client.get('/analytics/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_dashboard_redirects_non_staff_user(self):
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        # Non-staff gets redirected
        self.assertIn(response.status_code, [302, 403])

    def test_dashboard_accessible_by_staff(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_context_has_stats(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        self.assertIn('stats', response.context)

    def test_dashboard_context_has_required_keys(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        ctx = response.context
        expected_keys = [
            'stats', 'daily_sales', 'top_products',
            'latest_orders', 'low_stock', 'monthly_revenue', 'status_breakdown',
        ]
        for key in expected_keys:
            self.assertIn(key, ctx, f"Missing context key: {key}")

    def test_dashboard_stats_keys(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        expected_stat_keys = [
            'total_revenue', 'monthly_revenue', 'total_orders',
            'monthly_orders', 'total_customers', 'new_customers', 'avg_order_value',
        ]
        for key in expected_stat_keys:
            self.assertIn(key, stats, f"Missing stats key: {key}")

    def test_dashboard_stats_initial_values_are_zero(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        self.assertEqual(stats['total_revenue'], 0)
        self.assertEqual(stats['total_orders'], 0)

    def test_dashboard_counts_paid_orders_only(self):
        category = Category.objects.create(name='Analytics Cat')
        product = Product.objects.create(
            name='Analytics Product', category=category,
            description='Test', price=Decimal('50.00'), stock_quantity=10, is_active=True,
        )
        customer = User.objects.create_user(username='customer1', password='testpass123')
        paid_order = Order.objects.create(
            user=customer,
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            shipping_address='5 Analytic Ave',
            billing_address='5 Analytic Ave',
            email='customer@example.com',
            payment_status='paid',
        )
        OrderItem.objects.create(
            order=paid_order, product=product,
            product_name='Analytics Product', quantity=1,
            unit_price=Decimal('50.00'), total_price=Decimal('50.00'),
        )
        pending_order = Order.objects.create(
            user=customer,
            subtotal=Decimal('30.00'),
            total_amount=Decimal('30.00'),
            shipping_address='5 Analytic Ave',
            billing_address='5 Analytic Ave',
            email='customer@example.com',
            payment_status='pending',
        )

        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        # Only paid orders counted
        self.assertEqual(stats['total_orders'], 1)
        self.assertEqual(stats['total_revenue'], Decimal('50.00'))

    def test_dashboard_excludes_staff_from_customer_count(self):
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/analytics/dashboard/')
        stats = response.context['stats']
        # regularuser is non-staff, staffuser is staff → only 1 customer
        self.assertEqual(stats['total_customers'], 1)
