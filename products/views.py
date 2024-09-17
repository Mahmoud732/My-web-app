from django.shortcuts import render
from .models import Product
# Create your views here.
def product(request):
    return render(request, 'products/product.html', {'products':Product.objects.all()})

def products(request):
    return render(request, 'products/products.html', {'products':Product.objects.all()})