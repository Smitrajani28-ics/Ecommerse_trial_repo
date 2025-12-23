from django.test import TestCase
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Order, OrderItem, OrderStatusHistory
from decimal import Decimal


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            description='Test description',
            price=Decimal('99.99'),
            stock_quantity=10
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('99.99'),
            total_amount=Decimal('99.99'),
            shipping_address='123 Test St, Test City, TC 12345',
            billing_address='123 Test St, Test City, TC 12345',
            email='test@example.com'
        )

    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.status, 'pending')
        self.assertEqual(self.order.payment_status, 'pending')
        self.assertEqual(self.order.subtotal, Decimal('99.99'))
        self.assertEqual(self.order.total_amount, Decimal('99.99'))
        self.assertTrue(self.order.order_number)  # Should be auto-generated

    def test_order_str_representation(self):
        expected_str = f"Order {self.order.order_number}"
        self.assertEqual(str(self.order), expected_str)

    def test_order_number_generation(self):
        # Order number should be 12 characters long
        self.assertEqual(len(self.order.order_number), 12)
        
        # Should be unique
        order2 = Order.objects.create(
            user=self.user,
            subtotal=Decimal('50.00'),
            total_amount=Decimal('50.00'),
            shipping_address='456 Test Ave, Test City, TC 54321',
            billing_address='456 Test Ave, Test City, TC 54321',
            email='test2@example.com'
        )
        self.assertNotEqual(self.order.order_number, order2.order_number)

    def test_order_properties(self):
        # Test can_be_cancelled
        self.assertTrue(self.order.can_be_cancelled)
        
        # Test is_paid
        self.assertFalse(self.order.is_paid)
        
        # Test total_items (no items yet)
        self.assertEqual(self.order.total_items, 0)

    def test_calculate_total(self):
        self.order.subtotal = Decimal('100.00')
        self.order.tax_amount = Decimal('8.00')
        self.order.shipping_cost = Decimal('10.00')
        self.order.discount_amount = Decimal('5.00')
        
        calculated_total = self.order.calculate_total()
        expected_total = Decimal('113.00')  # 100 + 8 + 10 - 5
        
        self.assertEqual(calculated_total, expected_total)
        self.assertEqual(self.order.total_amount, expected_total)

    def test_mark_as_paid(self):
        self.order.mark_as_paid()
        
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'processing')
        self.assertTrue(self.order.is_paid)

    def test_cancel_order_success(self):
        # Add an order item first
        order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        
        initial_stock = self.product.stock_quantity
        result = self.order.cancel_order()
        
        self.assertTrue(result)
        self.assertEqual(self.order.status, 'cancelled')
        
        # Check stock was restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock + 2)

    def test_cancel_order_not_allowed(self):
        self.order.status = 'delivered'
        self.order.save()
        
        result = self.order.cancel_order()
        self.assertFalse(result)
        self.assertEqual(self.order.status, 'delivered')


class OrderItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            description='Test description',
            price=Decimal('99.99'),
            stock_quantity=10,
            sku='TEST-001'
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('199.98'),
            total_amount=Decimal('199.98'),
            shipping_address='123 Test St, Test City, TC 12345',
            billing_address='123 Test St, Test City, TC 12345',
            email='test@example.com'
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )

    def test_order_item_creation(self):
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.unit_price, self.product.price)
        self.assertEqual(self.order_item.product_name, self.product.name)
        self.assertEqual(self.order_item.product_sku, self.product.sku)

    def test_order_item_str_representation(self):
        expected_str = f"2 x {self.product.name}"
        self.assertEqual(str(self.order_item), expected_str)

    def test_order_item_total_price_calculation(self):
        expected_total = self.order_item.quantity * self.order_item.unit_price
        self.assertEqual(self.order_item.total_price, expected_total)
        self.assertEqual(self.order_item.get_total_price, expected_total)

    def test_order_item_saves_product_info(self):
        # Product info should be saved for historical purposes
        self.assertEqual(self.order_item.product_name, self.product.name)
        self.assertEqual(self.order_item.product_sku, self.product.sku)

    def test_order_total_items_property(self):
        # Create another order item
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            unit_price=Decimal('50.00')
        )
        
        # Total items should be sum of all quantities
        self.assertEqual(self.order.total_items, 5)  # 2 + 3


class OrderStatusHistoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        self.order = Order.objects.create(
            user=self.user,
            subtotal=Decimal('99.99'),
            total_amount=Decimal('99.99'),
            shipping_address='123 Test St, Test City, TC 12345',
            billing_address='123 Test St, Test City, TC 12345',
            email='test@example.com'
        )
        self.status_history = OrderStatusHistory.objects.create(
            order=self.order,
            status='processing',
            notes='Order is being processed',
            created_by=self.admin_user
        )

    def test_status_history_creation(self):
        self.assertEqual(self.status_history.order, self.order)
        self.assertEqual(self.status_history.status, 'processing')
        self.assertEqual(self.status_history.notes, 'Order is being processed')
        self.assertEqual(self.status_history.created_by, self.admin_user)

    def test_status_history_str_representation(self):
        expected_str = f"{self.order.order_number} - Processing"
        self.assertEqual(str(self.status_history), expected_str)
