from django.test import TestCase
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Cart, CartItem
from decimal import Decimal


class CartModelTest(TestCase):
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
        self.cart = Cart.objects.create(user=self.user)

    def test_cart_creation(self):
        self.assertEqual(self.cart.user, self.user)
        self.assertTrue(self.cart.is_empty)
        self.assertEqual(self.cart.total_items, 0)
        self.assertEqual(self.cart.total_price, 0)

    def test_cart_str_representation(self):
        expected_str = f"Cart for {self.user.username}"
        self.assertEqual(str(self.cart), expected_str)

    def test_anonymous_cart_str_representation(self):
        anonymous_cart = Cart.objects.create(session_key='test_session_key')
        expected_str = "Anonymous Cart (test_session_key)"
        self.assertEqual(str(anonymous_cart), expected_str)

    def test_cart_with_items(self):
        # Add item to cart
        cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        self.assertFalse(self.cart.is_empty)
        self.assertEqual(self.cart.total_items, 2)
        self.assertEqual(self.cart.total_price, Decimal('199.98'))

    def test_cart_clear(self):
        # Add item to cart
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )
        
        self.assertFalse(self.cart.is_empty)
        
        # Clear cart
        self.cart.clear()
        self.assertTrue(self.cart.is_empty)
        self.assertEqual(self.cart.total_items, 0)


class CartItemModelTest(TestCase):
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
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2
        )

    def test_cart_item_creation(self):
        self.assertEqual(self.cart_item.cart, self.cart)
        self.assertEqual(self.cart_item.product, self.product)
        self.assertEqual(self.cart_item.quantity, 2)

    def test_cart_item_str_representation(self):
        expected_str = f"2 x {self.product.name}"
        self.assertEqual(str(self.cart_item), expected_str)

    def test_cart_item_total_price(self):
        expected_total = self.cart_item.quantity * self.product.price
        self.assertEqual(self.cart_item.total_price, expected_total)
        self.assertEqual(self.cart_item.get_total_price(), expected_total)

    def test_increase_quantity_success(self):
        initial_quantity = self.cart_item.quantity
        result = self.cart_item.increase_quantity(2)
        
        self.assertTrue(result)
        self.assertEqual(self.cart_item.quantity, initial_quantity + 2)

    def test_increase_quantity_insufficient_stock(self):
        initial_quantity = self.cart_item.quantity
        result = self.cart_item.increase_quantity(20)  # More than available stock
        
        self.assertFalse(result)
        self.assertEqual(self.cart_item.quantity, initial_quantity)

    def test_decrease_quantity_success(self):
        initial_quantity = self.cart_item.quantity
        result = self.cart_item.decrease_quantity(1)
        
        self.assertTrue(result)
        self.assertEqual(self.cart_item.quantity, initial_quantity - 1)

    def test_decrease_quantity_to_zero(self):
        result = self.cart_item.decrease_quantity(2)  # Same as current quantity
        
        self.assertTrue(result)
        # Item should be deleted
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())

    def test_decrease_quantity_more_than_available(self):
        initial_quantity = self.cart_item.quantity
        result = self.cart_item.decrease_quantity(5)  # More than current quantity
        
        self.assertFalse(result)
        self.assertEqual(self.cart_item.quantity, initial_quantity)

    def test_update_quantity_success(self):
        result = self.cart_item.update_quantity(5)
        
        self.assertTrue(result)
        self.assertEqual(self.cart_item.quantity, 5)

    def test_update_quantity_to_zero(self):
        result = self.cart_item.update_quantity(0)
        
        self.assertTrue(result)
        # Item should be deleted
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())

    def test_update_quantity_insufficient_stock(self):
        initial_quantity = self.cart_item.quantity
        result = self.cart_item.update_quantity(20)  # More than available stock
        
        self.assertFalse(result)
        self.assertEqual(self.cart_item.quantity, initial_quantity)

    def test_unique_cart_product_constraint(self):
        # Try to create another cart item with same cart and product
        with self.assertRaises(Exception):  # Should raise IntegrityError
            CartItem.objects.create(
                cart=self.cart,
                product=self.product,
                quantity=1
            )
