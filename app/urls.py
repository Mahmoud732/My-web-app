from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('singup', views.singup, name='SingupPage'),
    path('login', views.login, name='LoginPage'),
    path('forgot-password', views.forgot_password, name='ForgotPage'),
    path('reset-password', views.reset_password, name='resetPage')
]