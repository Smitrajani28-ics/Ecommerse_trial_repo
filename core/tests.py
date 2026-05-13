from django.test import TestCase, Client
from products.models import Category, Product
from core.sitemaps import ProductSitemap, CategorySitemap, StaticSitemap


class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Home Cat', is_active=True)
        self.featured = Product.objects.create(
            name='Featured Product', category=self.category,
            description='Featured', price=10.00, stock_quantity=5,
            is_active=True, is_featured=True,
        )
        self.regular = Product.objects.create(
            name='Regular Product', category=self.category,
            description='Regular', price=20.00, stock_quantity=3,
            is_active=True, is_featured=False,
        )
        self.inactive = Product.objects.create(
            name='Inactive Product', category=self.category,
            description='Inactive', price=5.00, stock_quantity=1,
            is_active=False,
        )

    def test_home_returns_200(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_context_has_featured_products(self):
        response = self.client.get('/')
        self.assertIn('featured_products', response.context)

    def test_home_context_has_categories(self):
        response = self.client.get('/')
        self.assertIn('categories', response.context)

    def test_home_context_has_latest_products(self):
        response = self.client.get('/')
        self.assertIn('latest_products', response.context)

    def test_featured_products_only_active_and_featured(self):
        response = self.client.get('/')
        featured = list(response.context['featured_products'])
        self.assertIn(self.featured, featured)
        self.assertNotIn(self.regular, featured)
        self.assertNotIn(self.inactive, featured)

    def test_latest_products_excludes_inactive(self):
        response = self.client.get('/')
        latest = list(response.context['latest_products'])
        self.assertNotIn(self.inactive, latest)
        self.assertIn(self.regular, latest)

    def test_categories_only_active(self):
        inactive_cat = Category.objects.create(name='Inactive Cat', is_active=False)
        response = self.client.get('/')
        categories = list(response.context['categories'])
        self.assertIn(self.category, categories)
        self.assertNotIn(inactive_cat, categories)

    def test_featured_products_capped_at_eight(self):
        # Create 10 featured products
        for i in range(10):
            Product.objects.create(
                name=f'Extra Featured {i}', category=self.category,
                description='Extra', price=float(i + 1), stock_quantity=1,
                is_active=True, is_featured=True,
            )
        response = self.client.get('/')
        self.assertLessEqual(len(response.context['featured_products']), 8)

    def test_latest_products_capped_at_eight(self):
        for i in range(10):
            Product.objects.create(
                name=f'Extra Latest {i}', category=self.category,
                description='Extra', price=float(i + 1), stock_quantity=1,
                is_active=True,
            )
        response = self.client.get('/')
        self.assertLessEqual(len(response.context['latest_products']), 8)


class ProductSitemapTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='SiteMap Cat', is_active=True)
        self.active_product = Product.objects.create(
            name='Sitemap Active', category=self.category,
            description='Active', price=10.00, stock_quantity=5, is_active=True,
        )
        self.inactive_product = Product.objects.create(
            name='Sitemap Inactive', category=self.category,
            description='Inactive', price=10.00, stock_quantity=5, is_active=False,
        )

    def test_product_sitemap_only_active(self):
        sitemap = ProductSitemap()
        items = list(sitemap.items())
        self.assertIn(self.active_product, items)
        self.assertNotIn(self.inactive_product, items)

    def test_product_sitemap_lastmod(self):
        sitemap = ProductSitemap()
        lastmod = sitemap.lastmod(self.active_product)
        self.assertEqual(lastmod, self.active_product.updated_at)

    def test_product_sitemap_changefreq(self):
        self.assertEqual(ProductSitemap.changefreq, 'weekly')

    def test_product_sitemap_priority(self):
        self.assertAlmostEqual(ProductSitemap.priority, 0.8)


class CategorySitemapTest(TestCase):
    def setUp(self):
        self.active_cat = Category.objects.create(name='Active Sitemap Cat', is_active=True)
        self.inactive_cat = Category.objects.create(name='Inactive Sitemap Cat', is_active=False)

    def test_category_sitemap_only_active(self):
        sitemap = CategorySitemap()
        items = list(sitemap.items())
        self.assertIn(self.active_cat, items)
        self.assertNotIn(self.inactive_cat, items)

    def test_category_sitemap_location(self):
        sitemap = CategorySitemap()
        location = sitemap.location(self.active_cat)
        self.assertEqual(location, self.active_cat.get_absolute_url())

    def test_category_sitemap_changefreq(self):
        self.assertEqual(CategorySitemap.changefreq, 'weekly')


class StaticSitemapTest(TestCase):
    def test_static_sitemap_items(self):
        sitemap = StaticSitemap()
        items = sitemap.items()
        self.assertIn('core:home', items)
        self.assertIn('products:product_list', items)

    def test_static_sitemap_location_resolves(self):
        sitemap = StaticSitemap()
        location = sitemap.location('core:home')
        self.assertTrue(location.startswith('/'))

    def test_static_sitemap_priority(self):
        self.assertAlmostEqual(StaticSitemap.priority, 1.0)

    def test_static_sitemap_changefreq(self):
        self.assertEqual(StaticSitemap.changefreq, 'monthly')
