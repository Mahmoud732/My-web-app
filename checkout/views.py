from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from cart.models import Cart
from generator.models import Token
from .forms import CheckoutForm
from .models import Order, OrderItem
from datetime import timedelta
from pymongo import MongoClient
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://mahmed732005:ddEcRyduRgwFmc3v@cluster0.us288kr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
client = MongoClient(MONGO_URI)
db = client['auth_app']
tokens_collection = db['tokens']

@login_required
def user_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by('-order_date')
    return render(request, 'checkout/user_orders.html', {'orders': orders})


@login_required
def checkout_view(request):
    try:
        cart, created = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('Cart')

        if request.method == 'POST':
            form = CheckoutForm(request.POST)
            if form.is_valid():
                order_total = sum(item.product.price * item.quantity for item in cart.items.all())
                order = Order.objects.create(
                    customer=request.user,
                    total_price=order_total,
                    shipping_address=form.cleaned_data['address'],
                )

                # Create OrderItems for each item in the cart
                for item in cart.items.all():
                    # Use the product's activation period for time
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        time=item.product.activation_period,  # Make sure this field is defined in Product
                        price=item.product.price,
                    )

                # Clear cart after placing the order
                cart.items.all().delete()
                order.payment_status = 'C'
                order.save()
                messages.success(request, 'Order placed successfully!')
                return redirect('order_confirmation', order_id=order.id)
        
        else:
            form = CheckoutForm()
        
        total_price = sum(item.product.price * item.quantity for item in cart.items.all())
        context = {
            'form': form,
            'cart_items': cart.items.all(),
            'total_price': total_price,
        }
    
    except Exception as e:
        logger.error(f'Error during checkout for user {request.user.username}: {e}')
        messages.error(request, 'An error occurred during checkout. Please try again.')
        context = {
            'form': CheckoutForm(),
            'cart_items': [],
            'total_price': 0,
        }
    
    return render(request, 'checkout/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if request.method == 'POST':
        # Generate the token for the order
        if not order.token_activated:
            request.session['order_id'] = order_id
            request.session['validation_id'] = True
            return redirect('generate_token')
        else:
            messages.info(request, 'Token already exists.')
            return redirect('Orders')
    return render(request, 'checkout/order_confirmation.html', {'order': order})
