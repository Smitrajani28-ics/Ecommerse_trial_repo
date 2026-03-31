from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from products.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='orderuser', password='testpass123')
        self.category = Category.objects.create(name='Cat')
        self.product = Product.objects.create(
            name='Order Product', category=self.category,
            description='Test', price=25.00, stock_quantity=10, is_active=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('50.00'),
            tax_amount=Decimal('4.00'),
            total_amount=Decimal('54.00'),
            shipping_address='123 Test St\nTest City, TS 12345',
            billing_address='123 Test St\nTest City, TS 12345',
            email='test@example.com',
        )
        OrderItem.objects.create(
            order=self.order, product=self.product,
            product_name='Order Product', quantity=2,
            unit_price=Decimal('25.00'), total_price=Decimal('50.00'),
        )

    def test_order_number_generated(self):
        self.assertTrue(len(self.order.order_number) > 0)

    def test_order_total_items(self):
        self.assertEqual(self.order.total_items, 2)

    def test_order_can_be_cancelled(self):
        self.assertTrue(self.order.can_be_cancelled)

    def test_cancel_order(self):
        self.assertTrue(self.order.cancel_order())
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')

    def test_mark_as_paid(self):
        self.order.mark_as_paid()
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'processing')


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='checkoutuser', password='testpass123')
        self.category = Category.objects.create(name='Cat')
        self.product = Product.objects.create(
            name='Checkout Product', category=self.category,
            description='Test', price=30.00, stock_quantity=10, is_active=True,
        )

    def test_checkout_requires_login(self):
        response = self.client.get('/orders/create/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_checkout_empty_cart_redirects(self):
        self.client.login(username='checkoutuser', password='testpass123')
        response = self.client.get('/orders/create/')
        self.assertEqual(response.status_code, 302)

    def test_order_history_requires_login(self):
        response = self.client.get('/orders/history/')
        self.assertEqual(response.status_code, 302)
