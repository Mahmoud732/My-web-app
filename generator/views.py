from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from checkout.models import Order
from generator.models import Token
from pymongo import MongoClient
from datetime import timedelta
import os
import secrets
import logging

# Set up logging
logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://mahmed732005:ddEcRyduRgwFmc3v@cluster0.us288kr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
client = MongoClient(MONGO_URI)
db = client['auth_app']
tokens_collection = db['tokens']

@login_required
def generate_token(request):
    validation_id = request.session.pop('validation_id', None)
    if not validation_id:
        messages.error(request, 'Invalid or expired request!')
        return redirect(request.META.get('HTTP_REFERER', 'fallback_error_view'))  # Replace with an actual error view

    # Retrieve the order ID from the session
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'No order found in session.')
        return redirect('Orders')  # Redirect to orders or an appropriate page

    # Fetch the order object
    order = get_object_or_404(Order, id=order_id, customer=request.user)

    # Calculate total time based on the quantity of items
    total_hours = sum(item.quantity * item.time.total_seconds() / 3600 for item in order.items.all())  # Convert time to hours
    TOKEN_EXPIRATION = timedelta(hours=total_hours)

    token = secrets.token_hex(16)
    created_at = timezone.now()
    expiration = created_at + TOKEN_EXPIRATION

    # Prepare token data for MongoDB
    token_data = {
        'user_id': '',
        'token': token,
        'createdAt': created_at,
        'expiresAt': expiration,
        'purpose': 'purchase'
    }

    try:
        # Insert the token data into MongoDB
        tokens_collection.insert_one(token_data)
        
        # Save the token in the Django model as well
        user_token = Token.objects.create(token=token, user=request.user, order=order, created_at=created_at, expires_at=expiration)
        
        # Update order status and token activation
        order.token_activated = True
        order.status = 'C'  # Assuming 'C' stands for Completed
        order.save()
    except Exception as e:
        logger.error(f'Database error: {e}')
        messages.error(request, 'Unable to save token. Please try again.')
        return redirect(request.META.get('HTTP_REFERER', 'fallback_error_view'))  # Replace with an actual fallback view

    # Token generation successful, render token info
    remaining_time = expiration - timezone.now()  # Calculate remaining time
    messages.success(request, 'Token generated successfully!')
    
    return render(request, 'generator/token_info.html', {
        'token': user_token.token,
        'expires_at': user_token.expires_at,
        'remaining_time': str(remaining_time)  # Convert to string for display
    })
