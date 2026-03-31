from django.test import TestCase, Client
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Cart, CartItem


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Test Cat')
        self.product = Product.objects.create(
            name='Test Product', category=self.category,
            description='Test', price=10.00, stock_quantity=20, is_active=True,
        )
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_cart_total_items(self):
        self.assertEqual(self.cart.total_items, 2)

    def test_cart_total_price(self):
        self.assertEqual(self.cart.total_price, 20.00)

    def test_cart_item_total_price(self):
        self.assertEqual(self.item.total_price, 20.00)

    def test_increase_quantity(self):
        self.assertTrue(self.item.increase_quantity(3))
        self.assertEqual(self.item.quantity, 5)

    def test_decrease_quantity(self):
        self.assertTrue(self.item.decrease_quantity(1))
        self.assertEqual(self.item.quantity, 1)

    def test_update_quantity(self):
        self.assertTrue(self.item.update_quantity(5))
        self.assertEqual(self.item.quantity, 5)

    def test_cart_clear(self):
        self.cart.clear()
        self.assertTrue(self.cart.is_empty)


class CartViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='cartuser', password='testpass123')
        self.category = Category.objects.create(name='Cat')
        self.product = Product.objects.create(
            name='Cart Product', category=self.category,
            description='Test', price=15.00, stock_quantity=10, is_active=True,
        )

    def test_cart_detail_view(self):
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart(self):
        self.client.login(username='cartuser', password='testpass123')
        response = self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 1)

    def test_remove_from_cart(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        response = self.client.post(f'/cart/remove/{self.product.id}/')
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(cart.is_empty)
