from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [    
    path('', views.home_view, name='Home'),
    path('shop', views.products_view, name='Shop'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('contact/', views.contact_view, name='Contact'),
    path('profile/', views.profile_view, name='profile'),
    path('messages/', views.view_messages, name='view_messages'),
]