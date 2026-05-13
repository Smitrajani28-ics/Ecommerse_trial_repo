import json
from decimal import Decimal
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from products.models import Category, Product
from .models import Cart, CartItem
from .context_processors import cart_context


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


class CartAddViewExtendedTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='adduser', password='testpass123')
        self.category = Category.objects.create(name='AddCat')
        self.product = Product.objects.create(
            name='Add Product', category=self.category,
            description='Test', price=Decimal('20.00'), stock_quantity=5, is_active=True,
        )

    def test_add_get_request_not_allowed(self):
        response = self.client.get(f'/cart/add/{self.product.id}/')
        self.assertEqual(response.status_code, 405)

    def test_add_inactive_product_returns_404(self):
        inactive = Product.objects.create(
            name='Inactive', category=self.category,
            description='Test', price=Decimal('10.00'), stock_quantity=5, is_active=False,
        )
        response = self.client.post(f'/cart/add/{inactive.id}/', {'quantity': 1})
        self.assertEqual(response.status_code, 404)

    def test_add_caps_quantity_at_stock(self):
        self.client.login(username='adduser', password='testpass123')
        # Request more than stock
        response = self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 100})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, self.product.stock_quantity)

    def test_add_existing_item_accumulates_quantity(self):
        self.client.login(username='adduser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 4)

    def test_add_returns_json_for_ajax_request(self):
        self.client.login(username='adduser', password='testpass123')
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

    def test_add_quantity_less_than_one_defaults_to_one(self):
        self.client.login(username='adduser', password='testpass123')
        response = self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 0})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 1)


class CartUpdateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='updateuser', password='testpass123')
        self.category = Category.objects.create(name='UpdateCat')
        self.product = Product.objects.create(
            name='Update Product', category=self.category,
            description='Test', price=Decimal('10.00'), stock_quantity=10, is_active=True,
        )
        self.client.login(username='updateuser', password='testpass123')
        # Add an item
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 3})

    def test_update_get_request_not_allowed(self):
        response = self.client.get(f'/cart/update/{self.product.id}/')
        self.assertEqual(response.status_code, 405)

    def test_update_changes_quantity(self):
        response = self.client.post(f'/cart/update/{self.product.id}/', {'quantity': 5})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, 5)

    def test_update_quantity_zero_removes_item(self):
        response = self.client.post(f'/cart/update/{self.product.id}/', {'quantity': 0})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertTrue(cart.is_empty)

    def test_update_quantity_exceeds_stock_caps_at_stock(self):
        response = self.client.post(f'/cart/update/{self.product.id}/', {'quantity': 999})
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.total_items, self.product.stock_quantity)

    def test_update_returns_json_for_ajax(self):
        response = self.client.post(
            f'/cart/update/{self.product.id}/',
            {'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('cart_total_items', data)
        self.assertIn('cart_total_price', data)

    def test_update_nonexistent_item_returns_404(self):
        other_product = Product.objects.create(
            name='Other', category=self.category,
            description='Test', price=Decimal('5.00'), stock_quantity=5, is_active=True,
        )
        response = self.client.post(f'/cart/update/{other_product.id}/', {'quantity': 1})
        self.assertEqual(response.status_code, 404)


class CartRemoveViewExtendedTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='removeuser', password='testpass123')
        self.category = Category.objects.create(name='RemoveCat')
        self.product = Product.objects.create(
            name='Remove Product', category=self.category,
            description='Test', price=Decimal('10.00'), stock_quantity=5, is_active=True,
        )
        self.client.login(username='removeuser', password='testpass123')
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})

    def test_remove_get_request_not_allowed(self):
        response = self.client.get(f'/cart/remove/{self.product.id}/')
        self.assertEqual(response.status_code, 405)

    def test_remove_returns_json_for_ajax(self):
        response = self.client.post(
            f'/cart/remove/{self.product.id}/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('cart_total_items', data)
        self.assertIn('cart_total_price', data)

    def test_remove_nonexistent_item_returns_404(self):
        other_product = Product.objects.create(
            name='NotInCart', category=self.category,
            description='Test', price=Decimal('5.00'), stock_quantity=5, is_active=True,
        )
        response = self.client.post(f'/cart/remove/{other_product.id}/')
        self.assertEqual(response.status_code, 404)


class CartContextProcessorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='ctxuser', password='testpass123')
        self.category = Category.objects.create(name='CtxCat')
        self.product = Product.objects.create(
            name='Ctx Product', category=self.category,
            description='Test', price=Decimal('30.00'), stock_quantity=10, is_active=True,
        )

    def _make_authenticated_request(self):
        request = self.factory.get('/')
        request.user = self.user
        session = SessionStore()
        session.create()
        request.session = session
        return request

    def _make_anonymous_request(self, session_key=None):
        request = self.factory.get('/')
        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()
        session = SessionStore()
        session.create()
        request.session = session
        return request

    def test_returns_cart_for_authenticated_user(self):
        Cart.objects.create(user=self.user)
        request = self._make_authenticated_request()
        ctx = cart_context(request)
        self.assertIsNotNone(ctx['cart'])

    def test_returns_none_cart_when_no_cart_exists(self):
        request = self._make_authenticated_request()
        ctx = cart_context(request)
        self.assertIsNone(ctx['cart'])

    def test_returns_none_cart_for_anonymous_user_without_session(self):
        request = self._make_anonymous_request()
        # No session key set on an active session, cart should be None
        ctx = cart_context(request)
        # cart may be None (no matching session cart)
        self.assertIn('cart', ctx)
        self.assertIn('coupon', ctx)
        self.assertIn('discount', ctx)

    def test_context_includes_required_keys(self):
        request = self._make_authenticated_request()
        ctx = cart_context(request)
        self.assertIn('cart', ctx)
        self.assertIn('coupon', ctx)
        self.assertIn('discount', ctx)

    def test_discount_defaults_to_zero_when_no_coupon(self):
        request = self._make_authenticated_request()
        ctx = cart_context(request)
        self.assertEqual(ctx['discount'], Decimal('0.00'))

    def test_coupon_defaults_to_none_when_no_coupon_in_session(self):
        request = self._make_authenticated_request()
        ctx = cart_context(request)
        self.assertIsNone(ctx['coupon'])
