from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from .models import UserProfile
from .forms import EditProfileForm
    
def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        birthday = request.POST.get('birthday')
        proxy_list = fetch_proxy_list()
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'registration/signup.html')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/signup.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken. Please choose a different one.')
            return render(request, 'registration/signup.html')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered. Please use a different one.')
            return render(request, 'registration/signup.html')
        try:
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, password=password, email=email)
            user.save()
            users_profile = UserProfile.objects.create(user=user, birthday=birthday)
            users_profile.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.username}')
            return redirect('Shop')
        except Exception as e:
            user.delete()
            messages.error(request, f'Error creating account: {e}')
    return render(request, 'registration/signup.html')

def login_view(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('Shop')
    if request.method == 'POST':
        login_id = request.POST.get('email')
        password = request.POST.get('password')
        if not login_id or not password:
            messages.error(request, 'Please enter both email/username and password.')
            return render(request, 'registration/login.html')
        user = authenticate(request, username=login_id, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('Shop')
        else:
            try:
                User.objects.get(username=login_id)
                messages.error(request, 'Incorrect password. Please try again.')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email/username.')
    return render(request, 'registration/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have logged out successfully.')
    else:
        messages.warning(request, 'You are not logged in.')
    return redirect('login')

class PasswordResetForm(forms.Form):
    email = forms.EmailField()

class PasswordResetView(FormView):
    template_name = 'registration/password_reset.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(self.request, 'No account found with this email address.')
            return self.form_invalid(form)

        current_site = get_current_site(self.request)
        subject = 'Password Reset Requested'
        message = render_to_string('registration/password_reset_email.html', {
            'email': user.email,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        messages.success(self.request, "We've sent you an email with instructions on how to reset your password.")
        return super().form_valid(form)

class PasswordResetDoneView(FormView):
    template_name = 'registration/password_reset_done.html'

@login_required
def profile_view(request):
    messages.info(request, 'You are viewing your profile.')
    return render(request, 'registration/profile.html', {'user': request.user})

@login_required
def edit_profile_view(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            firstname = form.cleaned_data['first_name']
            lastname = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            birthday = form.cleaned_data['birthday']
            # Check for email uniqueness
            if User.objects.filter(email=email).exclude(username=user.username).exists():
                messages.error(request, 'This email is already in use.')
            else:
                user.username = username
                user.email = email
                user.first_name = firstname
                user.last_name = lastname
                profile.birthday = birthday
                # Handle password change
                new_password = form.cleaned_data.get('new_password')
                if new_password:
                    user.set_password(new_password)
                    messages.success(request, 'Your password has been updated successfully.')
                user.save()
                profile.save()  # Save profile changes
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')
    else:
        form = EditProfileForm(instance=user, initial={'birthday': profile.birthday})
    return render(request, 'registration/edit_profile.html', {'form': form})

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = get_object_or_404(User, id=request.user.id)
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')
    return render(request, 'registration/delete_account.html')
