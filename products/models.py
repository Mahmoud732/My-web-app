from django.db import models

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
    price = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    image = models.ImageField(upload_to='Photos/%y/%m/%d', default='Photos/24/09/17/images.png')
    active = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = 'Product'
        ordering = ['name']
