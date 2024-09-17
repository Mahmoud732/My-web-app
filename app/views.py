from django.shortcuts import render
# from django.http import HttpResponse

# Create your views here.

def index(request):
    return render(request, 'app/index.html')

def about(request):
    return render(request, 'app/about.html')

def singup(request):
    return render(request, 'app/singup.html')

def login(request):
    data = {
        'username':'mahmoudahmed',
        'password':'1234'
    }
    return render(request, 'app/login.html', data)

def forgot_password(request):
    return render(request, 'app/forgot-password.html')

def reset_password(request):
    return render(request, 'app/reset-password.html')
