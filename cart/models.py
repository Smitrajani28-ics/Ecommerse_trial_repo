from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_key__isnull=False),
                name='cart_must_have_user_or_session'
            )
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Anonymous Cart ({self.session_key})"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    @property
    def is_empty(self):
        return not self.items.exists()

    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()

    def get_total_items(self):
        """Method version for template compatibility"""
        return self.total_items

    def get_total_price(self):
        """Method version for template compatibility"""
        return self.total_price


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']
        indexes = [
            models.Index(fields=['cart', 'product']),
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

    def get_total_price(self):
        """Method version for template compatibility"""
        return self.total_price

    def increase_quantity(self, amount=1):
        """Increase quantity by specified amount"""
        if self.product.stock_quantity >= self.quantity + amount:
            self.quantity += amount
            self.save()
            return True
        return False

    def decrease_quantity(self, amount=1):
        """Decrease quantity by specified amount"""
        if self.quantity > amount:
            self.quantity -= amount
            self.save()
            return True
        elif self.quantity == amount:
            self.delete()
            return True
        return False

    def update_quantity(self, new_quantity):
        """Update quantity to specific value"""
        if new_quantity <= 0:
            self.delete()
            return True
        elif self.product.stock_quantity >= new_quantity:
            self.quantity = new_quantity
            self.save()
            return True
        return False
