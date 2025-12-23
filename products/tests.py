from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from decimal import Decimal
from .models import Category, Product, ProductImage


class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices and gadgets"
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.slug, "electronics")
        self.assertTrue(self.category.is_active)

    def test_category_str_representation(self):
        self.assertEqual(str(self.category), "Electronics")

    def test_category_slug_auto_generation(self):
        category = Category.objects.create(name="Home & Garden")
        self.assertEqual(category.slug, "home-garden")

    def test_category_get_absolute_url(self):
        expected_url = reverse('products:product_list_by_category', args=[self.category.slug])
        self.assertEqual(self.category.get_absolute_url(), expected_url)


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            description="Electronic devices"
        )
        self.product = Product.objects.create(
            name="Smartphone",
            category=self.category,
            description="Latest smartphone with advanced features",
            price=Decimal('599.99'),
            stock_quantity=10
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Smartphone")
        self.assertEqual(self.product.slug, "smartphone")
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.price, Decimal('599.99'))
        self.assertEqual(self.product.stock_quantity, 10)
        self.assertTrue(self.product.is_active)

    def test_product_str_representation(self):
        self.assertEqual(str(self.product), "Smartphone")

    def test_product_slug_auto_generation(self):
        product = Product.objects.create(
            name="Gaming Laptop Pro",
            category=self.category,
            description="High-performance gaming laptop",
            price=Decimal('1299.99'),
            stock_quantity=5
        )
        self.assertEqual(product.slug, "gaming-laptop-pro")

    def test_product_get_absolute_url(self):
        expected_url = reverse('products:product_detail', args=[self.product.slug])
        self.assertEqual(self.product.get_absolute_url(), expected_url)

    def test_product_is_in_stock(self):
        self.assertTrue(self.product.is_in_stock)
        
        # Test out of stock
        self.product.stock_quantity = 0
        self.product.save()
        self.assertFalse(self.product.is_in_stock)

    def test_product_is_on_sale(self):
        # No sale initially
        self.assertFalse(self.product.is_on_sale)
        
        # Set compare price to create sale
        self.product.compare_price = Decimal('699.99')
        self.product.save()
        self.assertTrue(self.product.is_on_sale)

    def test_product_discount_percentage(self):
        self.product.compare_price = Decimal('699.99')
        self.product.save()
        expected_discount = int(((Decimal('699.99') - Decimal('599.99')) / Decimal('699.99')) * 100)
        self.assertEqual(self.product.discount_percentage, expected_discount)

    def test_reduce_stock(self):
        initial_stock = self.product.stock_quantity
        result = self.product.reduce_stock(3)
        self.assertTrue(result)
        self.assertEqual(self.product.stock_quantity, initial_stock - 3)

    def test_reduce_stock_insufficient(self):
        result = self.product.reduce_stock(15)  # More than available
        self.assertFalse(result)
        self.assertEqual(self.product.stock_quantity, 10)  # Should remain unchanged

    def test_increase_stock(self):
        initial_stock = self.product.stock_quantity
        self.product.increase_stock(5)
        self.assertEqual(self.product.stock_quantity, initial_stock + 5)

    def test_price_validation(self):
        # Test that price must be positive
        with self.assertRaises(ValidationError):
            product = Product(
                name="Invalid Product",
                category=self.category,
                description="Test product",
                price=Decimal('-10.00'),
                stock_quantity=1
            )
            product.full_clean()


class ProductImageModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            description="Test description",
            price=Decimal('99.99'),
            stock_quantity=5
        )

    def test_product_image_creation(self):
        image = ProductImage.objects.create(
            product=self.product,
            alt_text="Product main image",
            order=1
        )
        self.assertEqual(image.product, self.product)
        self.assertEqual(image.alt_text, "Product main image")
        self.assertEqual(image.order, 1)
        self.assertFalse(image.is_primary)

    def test_product_image_str_representation(self):
        image = ProductImage.objects.create(
            product=self.product,
            order=1
        )
        expected_str = f"{self.product.name} - Image 1"
        self.assertEqual(str(image), expected_str)
