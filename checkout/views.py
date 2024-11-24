from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from registration.models import UserProfile
from cart.models import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem
from .paymob_utils import get_auth_token, create_order, generate_payment_url
from pymongo import MongoClient
import hashlib
import hmac
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# MongoDB setup with secure environment variable
MONGO_URI = os.getenv('MONGO_URI')
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
                auth_token = get_auth_token()

                order_id = create_order(auth_token, order_total * 100)
                order = Order.objects.create(
                    id=order_id,
                    customer=request.user,
                    total_price=order_total,
                    shipping_address=form.cleaned_data['address'],
                )
                # Create OrderItems for each item in the cart
                for item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        time=item.product.activation_period,  # Ensure this field exists in Product model
                        price=item.product.price,
                    )

                # Clear cart after placing the order
                cart.items.all().delete()
                order.payment_status = 'P'  # Set as pending initially
                order.save()
                return redirect('start_payment', order_id=order.id)
        
        else:
            form = CheckoutForm()
        
        total_price = sum(item.product.price * item.quantity for item in cart.items.all())
        context = {
            'form': form,
            'cart_items': cart.items.all(),
            'total_price': total_price,
        }
    
    except Cart.DoesNotExist:
        logger.error(f'Cart does not exist for user {request.user.username}.')
        messages.error(request, 'An error occurred during checkout. Your cart could not be found.')
        context = {
            'form': CheckoutForm(),
            'cart_items': [],
            'total_price': 0,
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
def start_payment(request, order_id):
    try:
        user_data = get_object_or_404(UserProfile, user=request.user)
        auth_token = get_auth_token()
        order = get_object_or_404(Order, id=order_id, customer=request.user)
        amount_cents = int(order.total_price * 100)
        if amount_cents <= 0:
            messages.warning(request, 'Your cart is empty or the total is invalid.')
            return redirect('Cart')

        payment_token = generate_payment_url(user_data, auth_token, order_id, settings.PAYMOB_INTEGRATION_ID, amount_cents)

        # Retrieve iframe ID from settings for flexibility
        payment_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}"
        return redirect(payment_url)
    
    except UserProfile.DoesNotExist:
        logger.error(f'UserProfile not found for user {request.user.username}.')
        messages.error(request, 'Your profile could not be found. Please update your information.')
        return redirect('checkout')
    
    except Exception as e:
        logger.error(f"Error starting payment for user {request.user.username}: {e}")
        messages.error(request, 'An error occurred while starting the payment. Please try again.')
        return redirect('checkout')

@csrf_exempt
@login_required
def verify_payment(request):
    try:
        if request.method == 'GET':
            data = request.GET
            received_hmac = data.get("hmac")

            # Required keys for HMAC verification in exact order
            required_keys = [
                'amount_cents',
                'created_at',
                'currency',
                'error_occured',
                'has_parent_transaction',
                'id',
                'integration_id',
                'is_3d_secure',
                'is_auth',
                'is_capture',
                'is_refunded',
                'is_standalone_payment',
                'is_voided',
                'order',
                'owner',
                'pending',
                'source_data.pan',
                'source_data.sub_type',
                'source_data.type',
                'success'
            ]

            # Prepare concatenated string for HMAC calculation
            try:
                concatenated_string = ''.join(data.get(key, '') for key in required_keys)
            except KeyError as e:
                logger.error(f"Missing required data field: {e}")
                return JsonResponse({"message": f"Missing field: {e}"}, status=400)

            # Calculate HMAC
            calculated_hmac = hmac.new(
                key=settings.PAYMOB_HMAC_SECRET.encode(),
                msg=concatenated_string.encode(),
                digestmod=hashlib.sha512
            ).hexdigest()

            if received_hmac == calculated_hmac and data.get("success") == "true":
                order_id = data.get('order')
                order = get_object_or_404(Order, id=order_id, customer=request.user)

                if order.payment_status != 'C':  # Payment completion check
                    with transaction.atomic():
                        order.payment_status = 'C'  # Mark as completed
                        order.save()
                    logger.info(f"Payment verified successfully for order {order_id}")

                    # Set session variables to pass data to the token generator
                    request.session['order_id'] = order.id
                    request.session['validation_id'] = True

                    # Redirect to the token generator view
                    return redirect('generate_token', order_id=order.id)
                else:
                    logger.warning(f"Order {order_id} has already been completed.")
                    return redirect('generate_token', order_id=order.id)        
            else:
                logger.warning(f"Payment verification failed for order {data.get('order')}. Expected HMAC: {calculated_hmac}, received: {received_hmac}")
                return JsonResponse({"message": "Payment verification failed."}, status=400)

        return JsonResponse({"message": "Invalid request method. Only GET requests are allowed."}, status=405)

    except Order.DoesNotExist:
        logger.error(f"Order with ID {data.get('order')} not found for user {request.user.username}.")
        return JsonResponse({"message": "Order not found."}, status=404)

    except Exception as e:
        logger.error(f"Unexpected error during payment verification: {e}")
        return JsonResponse({"message": "An error occurred during payment verification."}, status=500)