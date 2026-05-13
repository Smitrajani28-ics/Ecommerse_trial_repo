from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Category, Product


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', description='Tech stuff')
        self.product = Product.objects.create(
            name='Test Phone',
            category=self.category,
            description='A test phone',
            price=999.99,
            stock_quantity=10,
            is_active=True,
        )

    def test_category_slug_auto_generated(self):
        self.assertEqual(self.category.slug, 'electronics')

    def test_product_slug_auto_generated(self):
        self.assertEqual(self.product.slug, 'test-phone')

    def test_product_is_in_stock(self):
        self.assertTrue(self.product.is_in_stock)

    def test_product_out_of_stock(self):
        self.product.stock_quantity = 0
        self.assertFalse(self.product.is_in_stock)

    def test_reduce_stock(self):
        self.assertTrue(self.product.reduce_stock(3))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 7)

    def test_reduce_stock_insufficient(self):
        self.assertFalse(self.product.reduce_stock(20))

    def test_discount_percentage(self):
        self.product.compare_price = 1299.99
        self.product.save()
        self.assertTrue(self.product.is_on_sale)
        self.assertGreater(self.product.discount_percentage, 0)


class ProductViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Books', is_active=True)
        self.product = Product.objects.create(
            name='Django Book',
            category=self.category,
            description='Learn Django',
            price=29.99,
            stock_quantity=5,
            is_active=True,
        )

    def test_product_list_view(self):
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Book')

    def test_product_list_by_category(self):
        response = self.client.get(f'/products/category/{self.category.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Book')

    def test_product_search(self):
        response = self.client.get('/products/?q=Django')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Book')

    def test_product_search_no_results(self):
        response = self.client.get('/products/?q=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No products found')

    def test_product_detail_view(self):
        response = self.client.get(f'/products/{self.product.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Book')
        self.assertContains(response, '29.99')

    def test_product_sort_by_price(self):
        response = self.client.get('/products/?sort=price_asc')
        self.assertEqual(response.status_code, 200)
