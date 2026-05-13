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


def make_order(user, **kwargs):
    defaults = {
        'subtotal': Decimal('100.00'),
        'total_amount': Decimal('100.00'),
        'shipping_address': '1 Main St\nCity, ST 00000',
        'billing_address': '1 Main St\nCity, ST 00000',
        'email': 'buyer@example.com',
    }
    defaults.update(kwargs)
    return Order.objects.create(user=user, **defaults)


def make_order_item(order, product, quantity=1, unit_price=None):
    price = unit_price or product.price
    return OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        quantity=quantity,
        unit_price=price,
        total_price=price * quantity,
    )


class ShipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='shipuser', password='testpass123')
        self.category = Category.objects.create(name='ShipCat')
        self.product = Product.objects.create(
            name='Ship Product', category=self.category,
            description='Test', price=Decimal('10.00'), stock_quantity=10, is_active=True,
        )
        self.order = make_order(self.user)

    def _make_shipment(self, carrier, tracking='TRACK123'):
        return Shipment.objects.create(
            order=self.order, carrier=carrier, tracking_number=tracking
        )

    def test_str_includes_order_number(self):
        shipment = self._make_shipment('usps')
        self.assertIn(self.order.order_number, str(shipment))

    def test_tracking_url_usps(self):
        shipment = self._make_shipment('usps', tracking='USPS123')
        self.assertIn('usps.com', shipment.tracking_url)
        self.assertIn('USPS123', shipment.tracking_url)

    def test_tracking_url_ups(self):
        shipment = self._make_shipment('ups', tracking='UPS456')
        self.assertIn('ups.com', shipment.tracking_url)
        self.assertIn('UPS456', shipment.tracking_url)

    def test_tracking_url_fedex(self):
        shipment = self._make_shipment('fedex', tracking='FDX789')
        self.assertIn('fedex.com', shipment.tracking_url)
        self.assertIn('FDX789', shipment.tracking_url)

    def test_tracking_url_dhl(self):
        shipment = self._make_shipment('dhl', tracking='DHL000')
        self.assertIn('dhl.com', shipment.tracking_url)
        self.assertIn('DHL000', shipment.tracking_url)

    def test_tracking_url_other_returns_empty_string(self):
        shipment = self._make_shipment('other', tracking='OTHER111')
        self.assertEqual(shipment.tracking_url, '')

    def test_shipment_is_one_to_one_with_order(self):
        self._make_shipment('ups')
        with self.assertRaises(Exception):
            # A second shipment for the same order should fail
            Shipment.objects.create(
                order=self.order, carrier='fedex', tracking_number='DUP'
            )


class ReturnRequestModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='retuser', password='testpass123')
        self.category = Category.objects.create(name='RetCat')
        self.product = Product.objects.create(
            name='Return Product', category=self.category,
            description='Test', price=Decimal('25.00'), stock_quantity=10, is_active=True,
        )
        self.order = make_order(self.user, subtotal=Decimal('50.00'), total_amount=Decimal('50.00'))
        self.order_item = make_order_item(self.order, self.product, quantity=2)
        self.return_request = ReturnRequest.objects.create(
            order=self.order,
            user=self.user,
            order_item=self.order_item,
            reason='defective',
            description='Product arrived broken.',
        )

    def test_str_includes_order_number(self):
        self.assertIn(self.order.order_number, str(self.return_request))

    def test_default_status_is_pending(self):
        self.assertEqual(self.return_request.status, 'pending')

    def test_approve_sets_status_and_refund_amount(self):
        self.return_request.approve()
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.status, 'approved')
        self.assertEqual(self.return_request.refund_amount, self.order_item.total_price)

    def test_approve_refund_amount_equals_order_item_total(self):
        self.return_request.approve()
        self.return_request.refresh_from_db()
        expected = self.order_item.unit_price * self.order_item.quantity
        self.assertEqual(self.return_request.refund_amount, expected)

    def test_process_refund_sets_status_to_refunded(self):
        self.return_request.approve()
        self.return_request.process_refund()
        self.return_request.refresh_from_db()
        self.assertEqual(self.return_request.status, 'refunded')

    def test_process_refund_marks_order_refunded_when_all_items_refunded(self):
        self.return_request.approve()
        initial_stock = self.product.stock_quantity
        self.return_request.process_refund()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'refunded')
        self.assertEqual(self.order.payment_status, 'refunded')

    def test_process_refund_restores_product_stock(self):
        initial_stock = self.product.stock_quantity
        self.return_request.approve()
        self.return_request.process_refund()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock + self.order_item.quantity)

    def test_process_refund_does_not_mark_order_refunded_when_pending_returns_remain(self):
        product2 = Product.objects.create(
            name='Second Product', category=self.category,
            description='Test2', price=Decimal('15.00'), stock_quantity=5, is_active=True,
        )
        order_item2 = make_order_item(self.order, product2, quantity=1)
        return_request2 = ReturnRequest.objects.create(
            order=self.order,
            user=self.user,
            order_item=order_item2,
            reason='wrong_item',
            description='Got wrong item.',
        )
        # Approve and refund first return only
        self.return_request.approve()
        self.return_request.process_refund()
        self.order.refresh_from_db()
        # Second return is still pending, so order should NOT be fully refunded
        self.assertNotEqual(self.order.status, 'refunded')


class OrderCouponCodeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='couponorduser', password='testpass123')

    def test_coupon_code_field_defaults_to_empty(self):
        order = make_order(self.user)
        self.assertEqual(order.coupon_code, '')

    def test_coupon_code_can_be_set(self):
        order = make_order(self.user, coupon_code='SAVE10')
        order.refresh_from_db()
        self.assertEqual(order.coupon_code, 'SAVE10')
