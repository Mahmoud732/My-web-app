from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from app.models import Product
from datetime import timedelta

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Completed'),
        ('S', 'Shipped'),
        ('R', 'Returned'),
        ('F', 'Failed'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Completed'),
        ('F', 'Failed'),
        ('R', 'Refunded'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_date = models.DateTimeField(auto_now_add=True)
    shipping_address = models.TextField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=1, choices=ORDER_STATUS_CHOICES, default='P')
    payment_status = models.CharField(max_length=1, choices=PAYMENT_STATUS_CHOICES, default='P')
    shipping_date = models.DateTimeField(null=True, blank=True)
    token_activated = models.BooleanField(default=False)

    def calculate_total(self):
        """Calculate total price based on associated OrderItems."""
        self.total_price = sum(item.get_total_price() for item in self.items.all())
        self.save()

    def update_order_status(self, new_status):
        """Update order status and handle related changes."""
        self.status = new_status
        if new_status == 'S':
            self.shipping_date = timezone.now()
        elif new_status == 'C':
            self.delivery_date = timezone.now()
        self.save()

    def __str__(self):
        return f"Order {self.id} by {self.customer.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    time = models.DurationField(default=timedelta(hours=0))  # Duration field to store time
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) - {self.get_total_price()}"

# Signals to automatically calculate order total after an order item save
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    instance.order.calculate_total()
