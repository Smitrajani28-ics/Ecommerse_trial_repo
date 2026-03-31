from django.db import models
from django.contrib.auth.models import User
from orders.models import Order


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('manual', 'Manual'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='stripe')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_client_secret = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - Order {self.order.order_number}"

    def mark_completed(self):
        self.status = 'completed'
        self.save()
        self.order.mark_as_paid()

    def mark_failed(self):
        self.status = 'failed'
        self.save()
        self.order.payment_status = 'failed'
        self.order.save()
