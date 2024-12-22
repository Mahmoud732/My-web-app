from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from .forms import ContactForm
from .models import ContactMessage
import logging

# Set up logging
logger = logging.getLogger(__name__)

def home_view(request):
    return render(request, 'app/home.html')

def error_view(request):
    return render(request, 'app/error.html')

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

