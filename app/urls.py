from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [    
    path('', views.home_view, name='Home'),
    path('contact', views.contact_view, name='Contact'),
    path('messages', views.view_messages, name='view_messages'),
]