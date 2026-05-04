from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal
import uuid


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True)
    shipping_address = models.TextField()
    billing_address = models.TextField()
    email = models.EmailField()
    phone = models.CharField(max_length=17, blank=True)
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        return str(uuid.uuid4()).replace('-', '').upper()[:12]

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'processing']

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    def calculate_total(self):
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        return self.total_amount

    def mark_as_paid(self):
        self.payment_status = 'paid'
        if self.status == 'pending':
            self.status = 'processing'
        self.save()

    def cancel_order(self):
        if self.can_be_cancelled:
            self.status = 'cancelled'
            self.save()
            for item in self.items.all():
                item.product.increase_stock(item.quantity)
            return True
        return False


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['order', 'product'])]

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_sku:
            self.product_sku = self.product.sku
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order Status Histories'

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"


class Shipment(models.Model):
    CARRIER_CHOICES = [
        ('usps', 'USPS'),
        ('ups', 'UPS'),
        ('fedex', 'FedEx'),
        ('dhl', 'DHL'),
        ('other', 'Other'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipment')
    carrier = models.CharField(max_length=20, choices=CARRIER_CHOICES)
    tracking_number = models.CharField(max_length=100)
    estimated_delivery = models.DateField(null=True, blank=True)
    shipped_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shipment for {self.order.order_number}"

    @property
    def tracking_url(self):
        urls = {
            'usps': f'https://tools.usps.com/go/TrackConfirmAction?tLabels={self.tracking_number}',
            'ups': f'https://www.ups.com/track?tracknum={self.tracking_number}',
            'fedex': f'https://www.fedex.com/fedextrack/?trknbr={self.tracking_number}',
            'dhl': f'https://www.dhl.com/en/express/tracking.html?AWB={self.tracking_number}',
        }
        return urls.get(self.carrier, '')


class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('received', 'Item Received'),
        ('refunded', 'Refunded'),
    ]

    REASON_CHOICES = [
        ('defective', 'Defective/Damaged'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not As Described'),
        ('no_longer_needed', 'No Longer Needed'),
        ('other', 'Other'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='return_requests')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Return #{self.id} - Order {self.order.order_number}"

    def approve(self):
        self.status = 'approved'
        self.refund_amount = self.order_item.total_price
        self.save()

    def process_refund(self):
        self.status = 'refunded'
        self.save()
        if not self.order.return_requests.exclude(status='refunded').exists():
            self.order.status = 'refunded'
            self.order.payment_status = 'refunded'
            self.order.save()
        self.order_item.product.increase_stock(self.order_item.quantity)
