from decimal import Decimal
from django.test import TestCase, Client
from products.models import Category, Product
from core.sitemaps import ProductSitemap, CategorySitemap, StaticSitemap


class HomeViewContextTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Home Cat', is_active=True)
        self.inactive_category = Category.objects.create(name='Inactive Cat', is_active=False)

    def _make_product(self, name, is_featured=False, is_active=True):
        return Product.objects.create(
            name=name,
            category=self.category,
            description='Test',
            price=Decimal('10.00'),
            stock_quantity=5,
            is_active=is_active,
            is_featured=is_featured,
        )

    def test_home_view_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_view_context_has_featured_products(self):
        self._make_product('Featured', is_featured=True)
        response = self.client.get('/')
        self.assertIn('featured_products', response.context)

    def test_featured_products_only_active_and_featured(self):
        featured = self._make_product('Featured', is_featured=True)
        inactive_featured = self._make_product('Inactive Featured', is_featured=True, is_active=False)
        active_not_featured = self._make_product('Not Featured', is_featured=False)
        response = self.client.get('/')
        featured_qs = list(response.context['featured_products'])
        self.assertIn(featured, featured_qs)
        self.assertNotIn(inactive_featured, featured_qs)
        self.assertNotIn(active_not_featured, featured_qs)

    def test_home_view_context_has_categories(self):
        response = self.client.get('/')
        self.assertIn('categories', response.context)

    def test_categories_only_includes_active(self):
        response = self.client.get('/')
        cats = list(response.context['categories'])
        self.assertIn(self.category, cats)
        self.assertNotIn(self.inactive_category, cats)

    def test_home_view_context_has_latest_products(self):
        self._make_product('Latest Product')
        response = self.client.get('/')
        self.assertIn('latest_products', response.context)

    def test_latest_products_only_active(self):
        active = self._make_product('Active Latest')
        inactive = self._make_product('Inactive Latest', is_active=False)
        response = self.client.get('/')
        latest = list(response.context['latest_products'])
        self.assertIn(active, latest)
        self.assertNotIn(inactive, latest)

    def test_featured_products_capped_at_eight(self):
        for i in range(12):
            self._make_product(f'Featured {i}', is_featured=True)
        response = self.client.get('/')
        self.assertLessEqual(len(list(response.context['featured_products'])), 8)

    def test_latest_products_capped_at_eight(self):
        for i in range(12):
            self._make_product(f'Product {i}')
        response = self.client.get('/')
        self.assertLessEqual(len(list(response.context['latest_products'])), 8)


class ProductSitemapTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Sitemap Cat', is_active=True)
        self.active_product = Product.objects.create(
            name='Active Sitemap Product',
            category=self.category,
            description='Test',
            price=Decimal('10.00'),
            stock_quantity=5,
            is_active=True,
        )
        self.inactive_product = Product.objects.create(
            name='Inactive Sitemap Product',
            category=self.category,
            description='Test',
            price=Decimal('10.00'),
            stock_quantity=5,
            is_active=False,
        )

    def test_items_returns_only_active_products(self):
        sitemap = ProductSitemap()
        items = list(sitemap.items())
        self.assertIn(self.active_product, items)
        self.assertNotIn(self.inactive_product, items)

    def test_lastmod_returns_updated_at(self):
        sitemap = ProductSitemap()
        self.assertEqual(sitemap.lastmod(self.active_product), self.active_product.updated_at)

    def test_changefreq_is_weekly(self):
        sitemap = ProductSitemap()
        self.assertEqual(sitemap.changefreq, 'weekly')

    def test_priority_is_0_8(self):
        sitemap = ProductSitemap()
        self.assertEqual(sitemap.priority, 0.8)


class CategorySitemapTest(TestCase):
    def setUp(self):
        self.active_cat = Category.objects.create(name='Active Sitemap Cat', is_active=True)
        self.inactive_cat = Category.objects.create(name='Inactive Sitemap Cat', is_active=False)

    def test_items_returns_only_active_categories(self):
        sitemap = CategorySitemap()
        items = list(sitemap.items())
        self.assertIn(self.active_cat, items)
        self.assertNotIn(self.inactive_cat, items)

    def test_location_returns_get_absolute_url(self):
        sitemap = CategorySitemap()
        self.assertEqual(sitemap.location(self.active_cat), self.active_cat.get_absolute_url())

    def test_changefreq_is_weekly(self):
        sitemap = CategorySitemap()
        self.assertEqual(sitemap.changefreq, 'weekly')

    def test_priority_is_0_6(self):
        sitemap = CategorySitemap()
        self.assertEqual(sitemap.priority, 0.6)


class StaticSitemapTest(TestCase):
    def test_items_returns_expected_url_names(self):
        sitemap = StaticSitemap()
        items = sitemap.items()
        self.assertIn('core:home', items)
        self.assertIn('products:product_list', items)

    def test_location_resolves_core_home(self):
        sitemap = StaticSitemap()
        location = sitemap.location('core:home')
        self.assertEqual(location, '/')

    def test_location_resolves_product_list(self):
        sitemap = StaticSitemap()
        location = sitemap.location('products:product_list')
        self.assertIsInstance(location, str)
        self.assertTrue(location.startswith('/'))

    def test_changefreq_is_monthly(self):
        sitemap = StaticSitemap()
        self.assertEqual(sitemap.changefreq, 'monthly')

    def test_priority_is_1_0(self):
        sitemap = StaticSitemap()
        self.assertEqual(sitemap.priority, 1.0)
