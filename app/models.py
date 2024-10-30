from django.db import models
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=20, default='newcategory')

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = 'Category'
        ordering = ['name']

class Product(models.Model):
    name = models.CharField(max_length=30, default='Product_Name')
    description = models.TextField(default='My_description', null=True, blank=True)
    price = models.DecimalField(max_digits=7, decimal_places=2, default=20.00)  # Increased max_digits for flexibility
    activation_period = models.DurationField(default=timedelta(hours=2))  # Duration field to store time
    image = models.ImageField(upload_to='Photos/%y/%m/%d', default='Photos/24/09/17/images.png')
    active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = 'Product'
        ordering = ['name']

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"