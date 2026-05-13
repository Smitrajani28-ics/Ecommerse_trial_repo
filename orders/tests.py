from django.test import TestCase, Client
from django.contrib.auth.models import User
from decimal import Decimal
from products.models import Category, Product
from cart.models import Cart, CartItem
from .models import Order, OrderItem, Shipment, ReturnRequest


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


class ShipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shipuser', password='testpass123')
        self.category = Category.objects.create(name='ShipCat')
        self.product = Product.objects.create(
            name='Ship Product', category=self.category,
            description='Test', price=Decimal('20.00'), stock_quantity=5, is_active=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('20.00'),
            total_amount=Decimal('20.00'),
            shipping_address='1 Ship St',
            billing_address='1 Ship St',
            email='ship@example.com',
        )

    def test_shipment_str(self):
        shipment = Shipment.objects.create(
            order=self.order, carrier='ups', tracking_number='1Z999AA10123456784',
        )
        self.assertIn(self.order.order_number, str(shipment))

    def test_tracking_url_ups(self):
        shipment = Shipment.objects.create(
            order=self.order, carrier='ups', tracking_number='TRACK123',
        )
        self.assertIn('TRACK123', shipment.tracking_url)
        self.assertIn('ups.com', shipment.tracking_url)

    def test_tracking_url_usps(self):
        shipment = Shipment.objects.create(
            order=self.order, carrier='usps', tracking_number='9400111899223463338341',
        )
        self.assertIn('usps.com', shipment.tracking_url)

    def test_tracking_url_fedex(self):
        shipment = Shipment.objects.create(
            order=self.order, carrier='fedex', tracking_number='449044304137821',
        )
        self.assertIn('fedex.com', shipment.tracking_url)

    def test_tracking_url_dhl(self):
        shipment = Shipment.objects.create(
            order=self.order, carrier='dhl', tracking_number='1234567890',
        )
        self.assertIn('dhl.com', shipment.tracking_url)

    def test_tracking_url_other_carrier_returns_empty(self):
        shipment = Shipment.objects.create(
            order=self.order, carrier='other', tracking_number='SOMETRACK',
        )
        self.assertEqual(shipment.tracking_url, '')

    def test_shipment_one_to_one_with_order(self):
        Shipment.objects.create(
            order=self.order, carrier='fedex', tracking_number='TRACK001',
        )
        self.assertTrue(hasattr(self.order, 'shipment'))


class ReturnRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='returnuser', password='testpass123')
        self.category = Category.objects.create(name='ReturnCat')
        self.product = Product.objects.create(
            name='Return Product', category=self.category,
            description='Test', price=Decimal('30.00'), stock_quantity=10, is_active=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('60.00'),
            total_amount=Decimal('60.00'),
            shipping_address='2 Return Rd',
            billing_address='2 Return Rd',
            email='return@example.com',
            status='delivered',
            payment_status='paid',
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, product=self.product,
            product_name='Return Product', quantity=2,
            unit_price=Decimal('30.00'), total_price=Decimal('60.00'),
        )
        self.return_request = ReturnRequest.objects.create(
            order=self.order,
            user=self.user,
            order_item=self.order_item,
            reason='defective',
            description='Product was broken on arrival.',
        )

    def test_return_request_str(self):
        result = str(self.return_request)
        self.assertIn('Return', result)
        self.assertIn(self.order.order_number, result)

    def test_return_request_default_status_is_pending(self):
        self.assertEqual(self.return_request.status, 'pending')

    def test_approve_sets_status_and_refund_amount(self):
        self.return_request.approve()
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.status, 'approved')
        self.assertEqual(self.return_request.refund_amount, self.order_item.total_price)

    def test_process_refund_sets_status_refunded(self):
        self.return_request.approve()
        self.return_request.process_refund()
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.status, 'refunded')

    def test_process_refund_marks_order_refunded_when_all_items_refunded(self):
        self.return_request.approve()
        self.return_request.process_refund()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'refunded')
        self.assertEqual(self.order.payment_status, 'refunded')

    def test_process_refund_restores_stock(self):
        initial_stock = self.product.stock_quantity
        self.return_request.approve()
        self.return_request.process_refund()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock + self.order_item.quantity)

    def test_return_request_ordering_newest_first(self):
        second = ReturnRequest.objects.create(
            order=self.order,
            user=self.user,
            order_item=self.order_item,
            reason='other',
            description='Changed mind.',
        )
        requests = list(ReturnRequest.objects.all())
        self.assertEqual(requests[0].pk, second.pk)


class OrderCouponCodeTest(TestCase):
    """Test that Order.coupon_code field (new in this PR) works correctly."""
    def setUp(self):
        self.user = User.objects.create_user(username='couponorderuser', password='testpass123')

    def test_order_with_coupon_code(self):
        order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('100.00'),
            total_amount=Decimal('90.00'),
            shipping_address='3 Coupon Lane',
            billing_address='3 Coupon Lane',
            email='coupon@example.com',
            coupon_code='SAVE10',
        )
        order.refresh_from_db()
        self.assertEqual(order.coupon_code, 'SAVE10')

    def test_order_coupon_code_defaults_to_blank(self):
        order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            shipping_address='4 No Coupon St',
            billing_address='4 No Coupon St',
            email='nocoupon@example.com',
        )
        self.assertEqual(order.coupon_code, '')
