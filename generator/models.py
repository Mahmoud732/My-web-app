from django.db import models
from django.utils import timezone
from registration.models import User
from checkout.models import Order
from datetime import timedelta
import secrets

EXPIRATION_TIME = timedelta(hours=2)

class Token(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True)
    token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, null=True)
    expires_at = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        # Generate token if it doesn't exist
        if not self.token:
            self.token = self.generate_token()
        # Set expiration based on created_at if expires_at is not set
        if not self.expires_at:
            EXPIRATION_TIME = timedelta(hours=2 * self.order.item.quantity)
            self.expires_at = self.created_at + EXPIRATION_TIME
        super().save(*args, **kwargs)

    def generate_token(self):
        # Generate a unique token
        while True:
            token = secrets.token_hex(16)
            if not Token.objects.filter(token=token).exists():
                return token

    def is_expired(self):
        # Check if the token has expired
        return timezone.now() > self.expires_at

    @property
    def remaining_time(self):
        remaining = self.expires_at - timezone.now()
        return max(remaining, timedelta(0))  # Ensures non-negative timedelta

    def __str__(self):
        return self.token or "No Token"
