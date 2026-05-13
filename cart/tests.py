import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from products.models import Category, Product
from .models import Cart, CartItem


def make_product(category, name='Test Product', price=10.00, stock=20):
    return Product.objects.create(
        name=name, category=category,
        description='Test', price=price,
        stock_quantity=stock, is_active=True,
    )


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.category = Category.objects.create(name='Test Cat')
        self.product = make_product(self.category)
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

    def test_cart_str_user(self):
        self.assertEqual(str(self.cart), f'Cart for {self.user.username}')

    def test_cart_str_anonymous(self):
        anon_cart = Cart.objects.create(session_key='abc123session')
        self.assertIn('abc123session', str(anon_cart))

    def test_increase_quantity_exceeds_stock_returns_false(self):
        # stock=20, current qty=2, request 19 more → total 21 > 20
        self.assertFalse(self.item.increase_quantity(19))
        self.assertEqual(self.item.quantity, 2)

    def test_decrease_quantity_to_zero_deletes_item(self):
        result = self.item.decrease_quantity(2)
        self.assertTrue(result)
        self.assertFalse(CartItem.objects.filter(pk=self.item.pk).exists())

    def test_decrease_quantity_more_than_current_returns_false(self):
        result = self.item.decrease_quantity(10)
        self.assertFalse(result)
        self.assertEqual(self.item.quantity, 2)

    def test_update_quantity_zero_deletes_item(self):
        result = self.item.update_quantity(0)
        self.assertTrue(result)
        self.assertFalse(CartItem.objects.filter(pk=self.item.pk).exists())

    def test_update_quantity_exceeds_stock_returns_false(self):
        result = self.item.update_quantity(100)
        self.assertFalse(result)
        self.assertEqual(self.item.quantity, 2)

    def test_cart_clear(self):
        self.cart.clear()
        self.assertTrue(self.cart.is_empty)

    def test_cart_is_empty_false_when_has_items(self):
        self.assertFalse(self.cart.is_empty)

    def test_get_total_price_method(self):
        self.assertEqual(self.cart.get_total_price(), self.cart.total_price)

    def test_get_total_items_method(self):
        self.assertEqual(self.cart.get_total_items(), self.cart.total_items)

    def test_cart_item_str(self):
        self.assertEqual(str(self.item), f'2 x {self.product.name}')


class CartViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='cartuser', password='testpass123')
        self.category = Category.objects.create(name='Cat')
        self.product = make_product(self.category, name='Cart Product', price=15.00, stock=10)

    def test_cart_detail_view(self):
        response = self.client.get('/cart/')
        self.assertEqual(response.status_code, 200)

    def test_add_to_cart(self):
        self.client.login(username='cartuser', password='testpass123')
        response = self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 1)

    def test_add_to_cart_requires_post(self):
        response = self.client.get(f'/cart/add/{self.product.id}/')
        self.assertEqual(response.status_code, 405)

    def test_add_to_cart_increments_existing_item(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 3})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 5)

    def test_add_to_cart_caps_at_stock_quantity(self):
        self.client.login(username='cartuser', password='testpass123')
        # Product has stock=10, try to add 100
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 100})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 10)

    def test_add_to_cart_ajax_returns_json(self):
        self.client.login(username='cartuser', password='testpass123')
        response = self.client.post(
            f'/cart/add/{self.product.id}/',
            {'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('cart_total_items', data)
        self.assertIn('message', data)

    def test_add_inactive_product_returns_404(self):
        inactive = Product.objects.create(
            name='Inactive', category=self.category,
            description='Test', price=10.00, stock_quantity=5, is_active=False,
        )
        self.client.login(username='cartuser', password='testpass123')
        response = self.client.post(f'/cart/add/{inactive.id}/', {'quantity': 1})
        self.assertEqual(response.status_code, 404)

    def test_remove_from_cart(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        response = self.client.post(f'/cart/remove/{self.product.id}/')
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(cart.is_empty)

    def test_remove_from_cart_requires_post(self):
        response = self.client.get(f'/cart/remove/{self.product.id}/')
        self.assertEqual(response.status_code, 405)

    def test_remove_from_cart_ajax_returns_json(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        response = self.client.post(
            f'/cart/remove/{self.product.id}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['cart_total_items'], 0)

    def test_cart_update_quantity(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 3})
        response = self.client.post(f'/cart/update/{self.product.id}/', {'quantity': 5})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 5)

    def test_cart_update_requires_post(self):
        response = self.client.get(f'/cart/update/{self.product.id}/')
        self.assertEqual(response.status_code, 405)

    def test_cart_update_quantity_zero_removes_item(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        response = self.client.post(f'/cart/update/{self.product.id}/', {'quantity': 0})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(cart.is_empty)

    def test_cart_update_exceeds_stock_caps_to_max(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        self.client.post(f'/cart/update/{self.product.id}/', {'quantity': 999})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 10)  # capped at stock=10

    def test_cart_update_ajax_returns_json(self):
        self.client.login(username='cartuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        response = self.client.post(
            f'/cart/update/{self.product.id}/',
            {'quantity': 4},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('cart_total_price', data)
        self.assertIn('item_total', data)

    def test_anonymous_user_can_add_to_cart(self):
        response = self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        self.assertEqual(response.status_code, 302)
        # Session cart should exist
        self.assertTrue(Cart.objects.filter(user__isnull=True).exists())
