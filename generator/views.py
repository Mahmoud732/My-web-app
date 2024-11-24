from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from time import time
from checkout.models import Order
from generator.models import Token
from pymongo import MongoClient
from datetime import timedelta
import json
import os
import secrets
import logging
import pytz

# Set up logging
logger = logging.getLogger(__name__)

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://mahmed732005:ddEcRyduRgwFmc3v@cluster0.r9g62.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
client = MongoClient(MONGO_URI)
db = client['auth_app']
tokens_collection = db['tokens']

TOKEN_RATE_LIMIT = (timedelta(seconds=30))

@login_required
def generate_token(request, order_id):
    validation_id = request.session.pop('validation_id', None)
    if not validation_id:
        messages.error(request, 'Invalid or expired request!')
        return redirect('Orders')

    # Fetch the order object
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    if order.payment_status != 'C':
        messages.error(request, 'You haven\'t paid')
        return redirect('Checkout')
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
        order.order_status = 'C'  # Assuming 'C' stands for Completed
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

# @login_required
@csrf_exempt
@require_POST
def validate_token(request):
    data = json.loads(request.body)
    token = data.get('token')
    user_id = data.get('user_id')
    if not token:
        return JsonResponse({"error": "Required Key."}, status=400)
    print(data)
    # Check rate limiting
    last_request_time = request.session.get('last_request_time')
    current_time = time()  # Current time as a UNIX timestamp
    if last_request_time and current_time < last_request_time + TOKEN_RATE_LIMIT.total_seconds():
        return JsonResponse({"error": "Many attempets, Please try again later."}, status=429)
    request.session['last_request_time'] = current_time  # Save current time as UNIX timestamp

    try:
        token_data = tokens_collection.find_one({"token": token})
    except Exception as e:
        logger.error(f"Database error: {e}")
        return JsonResponse({"error": "Can't connect to the Database."}, status=500)

    if token_data:
        # Ensure token_data['expiresAt'] is timezone-aware
        expires_at = token_data['expiresAt']
        if expires_at.tzinfo is None:  # Check if it's offset-naive
            expires_at = expires_at.replace(tzinfo=pytz.UTC)  # Make it UTC timezone-aware

        if timezone.now() > expires_at:
            return JsonResponse({"error": "Key has expired."}, status=400)

        if token_data['user_id'] and token_data['user_id'] != user_id:
            return JsonResponse({"error": "You have no access to this Key."}, status=403)

        if not token_data['user_id']:
            tokens_collection.update_one({"token": token}, {"$set": {"user_id": user_id}})

        # Validate purpose
        if token_data.get("purpose") != "purchase":
            return JsonResponse({"error": "You need to purchase This Key"}, status=400)

        return JsonResponse({"success": "Valid Key, Login Successfully!"}, status=200)
    else:
        return JsonResponse({"error": "Invalid Key"}, status=404)
    