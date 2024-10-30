from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cart
from app.models import Product
from cart.models import CartItem
import logging

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def cart_view(request):
    try:
        cart, created = Cart.objects.get_or_create(user=request.user)
        items = cart.items.all()
        total_price = sum(item.subtotal for item in items)

        context = {
            'items': items,
            'total_price': total_price,
            'item_count': items.count(),
            'cart_created': created,
        }
    except Exception as e:
        logger.error(f"Error retrieving cart: {e}")
        messages.error(request, "An error occurred while retrieving your cart. Please try again later.")
        context = {'items': [], 'total_price': 0, 'item_count': 0}

    return render(request, 'cart/cart.html', context)

@login_required
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

        cart_item.quantity += 1
        cart_item.save()
        
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        messages.error(request, f"An error occurred while adding {product.name} to your cart. Please try again later.")
    return redirect('Cart')

@login_required
def increment_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity += 1
        cart_item.save()
        
    except Exception as e:
        logger.error(f"Error incrementing item: {e}")
        messages.error(request, "An error occurred while updating the item quantity. Please try again later.")
    return redirect('Cart')

@login_required
def decrement_item(request, item_id):
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            
    except Exception as e:
        logger.error(f"Error decrementing item: {e}")
        messages.error(request, "An error occurred while updating the item quantity. Please try again later.")
    return redirect('Cart')
