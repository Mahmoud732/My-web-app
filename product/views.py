from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product
import logging


logger = logging.getLogger(__name__)

# Create your views here.
@login_required
def products_view(request):
    try:
        products = Product.objects.all()
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        messages.error(request, "An error occurred while fetching products. Please try again later.")
        products = []
    return render(request, 'product/shop.html', {'products': products})


def product_view(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        messages.error(request, "An error occurred while fetching product. Please try again later.")
    return render(request, 'product/product.html', {'product': product})