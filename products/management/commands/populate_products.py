from django.core.management.base import BaseCommand
from products.models import Category, Product
from decimal import Decimal
import requests
from django.core.files.base import ContentFile
import os


class Command(BaseCommand):
    help = 'Populate database with sample products and categories with images'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-images',
            action='store_true',
            help='Download and add images to products',
        )

    def download_image(self, url, filename):
        """Download image from URL and return ContentFile"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return ContentFile(response.content, filename)
        except Exception as e:
            self.stdout.write(f'Failed to download image: {e}')
        return None

    def handle(self, *args, **options):
        # Create categories with images
        categories_data = [
            {
                'name': 'Electronics', 
                'description': 'Electronic devices, gadgets, and tech accessories',
                'image_url': 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400'
            },
            {
                'name': 'Clothing', 
                'description': 'Fashion, apparel, and accessories for all occasions',
                'image_url': 'https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400'
            },
            {
                'name': 'Books', 
                'description': 'Books, literature, and educational materials',
                'image_url': 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400'
            },
            {
                'name': 'Home & Garden', 
                'description': 'Home improvement, furniture, and gardening supplies',
                'image_url': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400'
            },
            {
                'name': 'Sports & Fitness', 
                'description': 'Sports equipment, fitness gear, and outdoor activities',
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400'
            },
            {
                'name': 'Beauty & Health', 
                'description': 'Beauty products, skincare, and health supplements',
                'image_url': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400'
            },
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            
            # Add image if downloading is enabled and category was created
            if options['with_images'] and created and 'image_url' in cat_data:
                image_file = self.download_image(cat_data['image_url'], f"{category.slug}.jpg")
                if image_file:
                    category.image.save(f"{category.slug}.jpg", image_file, save=True)
            
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create comprehensive product catalog
        products_data = [
            # Electronics
            {
                'name': 'iPhone 15 Pro Max',
                'category': 'Electronics',
                'description': 'The most advanced iPhone ever with titanium design, A17 Pro chip, and professional camera system. Features include 5x telephoto zoom, Action Button, and USB-C connectivity.',
                'short_description': 'Latest iPhone with titanium design and A17 Pro chip',
                'price': Decimal('1199.99'),
                'compare_price': Decimal('1299.99'),
                'stock_quantity': 25,
                'is_featured': True,
                'weight': Decimal('221.0'),
                'dimensions': '159.9 x 76.7 x 8.25 mm',
                'image_url': 'https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=500'
            },
            {
                'name': 'MacBook Air M2',
                'category': 'Electronics',
                'description': 'Supercharged by the M2 chip, the redesigned MacBook Air combines incredible performance and up to 18 hours of battery life into its strikingly thin aluminum enclosure.',
                'short_description': 'Powerful laptop with M2 chip and all-day battery',
                'price': Decimal('1099.99'),
                'compare_price': Decimal('1199.99'),
                'stock_quantity': 15,
                'is_featured': True,
                'weight': Decimal('1240.0'),
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500'
            },
            {
                'name': 'Sony WH-1000XM5 Headphones',
                'category': 'Electronics',
                'description': 'Industry-leading noise canceling headphones with exceptional sound quality, 30-hour battery life, and crystal-clear hands-free calling.',
                'short_description': 'Premium noise-canceling wireless headphones',
                'price': Decimal('399.99'),
                'stock_quantity': 40,
                'weight': Decimal('250.0'),
                'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500'
            },
            {
                'name': 'Samsung 4K Smart TV 55"',
                'category': 'Electronics',
                'description': 'Crystal clear 4K resolution with HDR support, smart TV features, and voice control. Perfect for streaming, gaming, and entertainment.',
                'short_description': '55-inch 4K Smart TV with HDR',
                'price': Decimal('699.99'),
                'compare_price': Decimal('899.99'),
                'stock_quantity': 12,
                'weight': Decimal('15800.0'),
                'image_url': 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=500'
            },
            
            # Clothing
            {
                'name': 'Premium Cotton T-Shirt',
                'category': 'Clothing',
                'description': '100% organic cotton t-shirt with a comfortable fit. Available in multiple colors and sizes. Perfect for casual wear and layering.',
                'short_description': 'Comfortable organic cotton t-shirt',
                'price': Decimal('29.99'),
                'stock_quantity': 150,
                'weight': Decimal('180.0'),
                'image_url': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500'
            },
            {
                'name': 'Denim Jacket Classic',
                'category': 'Clothing',
                'description': 'Timeless denim jacket made from premium denim fabric. Features classic styling with modern fit. Perfect for layering in any season.',
                'short_description': 'Classic denim jacket with modern fit',
                'price': Decimal('89.99'),
                'compare_price': Decimal('119.99'),
                'stock_quantity': 45,
                'is_featured': True,
                'weight': Decimal('650.0'),
                'image_url': 'https://images.unsplash.com/photo-1544966503-7cc5ac882d5f?w=500'
            },
            {
                'name': 'Running Sneakers Pro',
                'category': 'Clothing',
                'description': 'High-performance running shoes with advanced cushioning technology, breathable mesh upper, and durable rubber outsole.',
                'short_description': 'Professional running shoes with advanced cushioning',
                'price': Decimal('149.99'),
                'stock_quantity': 60,
                'weight': Decimal('320.0'),
                'image_url': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500'
            },
            
            # Books
            {
                'name': 'Python Programming Mastery',
                'category': 'Books',
                'description': 'Comprehensive guide to Python programming covering basics to advanced topics. Includes practical examples, exercises, and real-world projects.',
                'short_description': 'Complete Python programming guide',
                'price': Decimal('49.99'),
                'stock_quantity': 80,
                'weight': Decimal('450.0'),
                'image_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500'
            },
            {
                'name': 'The Art of Web Design',
                'category': 'Books',
                'description': 'Learn modern web design principles, UX/UI best practices, and responsive design techniques. Perfect for beginners and professionals.',
                'short_description': 'Modern web design and UX principles',
                'price': Decimal('39.99'),
                'stock_quantity': 65,
                'weight': Decimal('380.0'),
                'image_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500'
            },
            
            # Home & Garden
            {
                'name': 'Smart Home Security Camera',
                'category': 'Home & Garden',
                'description': 'Wireless security camera with 1080p HD video, night vision, motion detection, and smartphone app control. Easy installation.',
                'short_description': 'Wireless HD security camera with app control',
                'price': Decimal('129.99'),
                'stock_quantity': 35,
                'is_featured': True,
                'weight': Decimal('280.0'),
                'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=500'
            },
            {
                'name': 'Indoor Plant Collection',
                'category': 'Home & Garden',
                'description': 'Set of 3 low-maintenance indoor plants perfect for home or office. Includes care instructions and decorative pots.',
                'short_description': 'Set of 3 indoor plants with decorative pots',
                'price': Decimal('79.99'),
                'stock_quantity': 25,
                'weight': Decimal('1200.0'),
                'image_url': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=500'
            },
            
            # Sports & Fitness
            {
                'name': 'Yoga Mat Premium',
                'category': 'Sports & Fitness',
                'description': 'High-quality yoga mat with superior grip and cushioning. Made from eco-friendly materials. Perfect for yoga, pilates, and fitness.',
                'short_description': 'Premium eco-friendly yoga mat',
                'price': Decimal('59.99'),
                'stock_quantity': 70,
                'weight': Decimal('900.0'),
                'image_url': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500'
            },
            {
                'name': 'Adjustable Dumbbells Set',
                'category': 'Sports & Fitness',
                'description': 'Space-saving adjustable dumbbells with quick weight change system. Ranges from 5-50 lbs per dumbbell. Perfect for home workouts.',
                'short_description': 'Adjustable dumbbells 5-50 lbs each',
                'price': Decimal('299.99'),
                'compare_price': Decimal('399.99'),
                'stock_quantity': 20,
                'is_featured': True,
                'weight': Decimal('22700.0'),
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500'
            },
            
            # Beauty & Health
            {
                'name': 'Skincare Routine Set',
                'category': 'Beauty & Health',
                'description': 'Complete skincare routine with cleanser, toner, serum, and moisturizer. Suitable for all skin types. Dermatologist tested.',
                'short_description': 'Complete 4-step skincare routine set',
                'price': Decimal('89.99'),
                'stock_quantity': 55,
                'weight': Decimal('320.0'),
                'image_url': 'https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500'
            },
            {
                'name': 'Vitamin D3 Supplements',
                'category': 'Beauty & Health',
                'description': 'High-potency Vitamin D3 supplements for immune support and bone health. 60 capsules, 2-month supply. Third-party tested.',
                'short_description': 'High-potency Vitamin D3 - 60 capsules',
                'price': Decimal('24.99'),
                'stock_quantity': 100,
                'weight': Decimal('85.0'),
                'image_url': 'https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=500'
            },
        ]

        for product_data in products_data:
            category_name = product_data.pop('category')
            image_url = product_data.pop('image_url', None)
            
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'category': categories[category_name],
                    **product_data
                }
            )
            
            # Add image if downloading is enabled and product was created
            if options['with_images'] and created and image_url:
                image_file = self.download_image(image_url, f"{product.slug}.jpg")
                if image_file:
                    product.image.save(f"{product.slug}.jpg", image_file, save=True)
            
            if created:
                self.stdout.write(f'Created product: {product.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with comprehensive product catalog')
        )