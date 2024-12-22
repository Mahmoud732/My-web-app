from django.urls import path, include
from django.contrib.auth import views
from . import views
urlpatterns = [    
    path('error', views.error_view, name='error_page'),
    path('contact', views.contact_view, name='Contact'),
    path('messages', views.view_messages, name='view_messages'),
]