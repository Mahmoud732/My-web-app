from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from registration.models import UserProfile
from app.models import Product
from .forms import ContactForm
from .models import ContactMessage
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home_view(request):
    return render(request, 'app/home.html')

@login_required
def products_view(request):
    try:
        products = Product.objects.all()
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        messages.error(request, "An error occurred while fetching products. Please try again later.")
        products = []
    return render(request, 'app/shop.html', {'products': products})

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
            )
            messages.success(request, "Thank you for contacting us! We will get back to you shortly.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'app/contact.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def view_messages(request):
    all_messages = ContactMessage.objects.all().order_by('-submitted_at')  # Order by most recent
    return render(request, 'app/messages.html', {'messages': all_messages})

@login_required
def profile_view(request):
    messages.info(request, 'You are viewing your profile.')
    return render(request, 'app/profile.html', {'user': request.user})

@login_required
def edit_profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        # Using a form to handle user input
        form = ContactForm(request.POST)  # Replace with a profile form
        if form.is_valid():
            firstname = form.cleaned_data['first_name']
            lastname = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            birthday = form.cleaned_data['birthday']
            if User.objects.filter(email=email).exclude(username=user.username).exists():
                messages.error(request, 'This email is already in use.')
            else:
                user.username = username
                user.email = email
                user.first_name = firstname
                user.last_name = lastname
                profile.birthday = birthday
                new_password = form.cleaned_data.get('new_password')
                confirm_password = form.cleaned_data.get('confirm_password')
                if new_password and new_password == confirm_password:
                    user.set_password(new_password)
                    messages.success(request, 'Your password has been updated successfully.')
                elif new_password and new_password != confirm_password:
                    messages.error(request, 'Passwords do not match. Please try again.')
                user.save()
                profile.save()  # Save profile changes
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
    else:
        data = {'birthday': profile.birthday}
    return render(request, 'app/edit_profile.html', data)

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = get_object_or_404(User, id=request.user.id)
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')
    return render(request, 'app/delete_account.html')
