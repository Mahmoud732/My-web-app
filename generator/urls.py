from django.urls import path
from . import views

urlpatterns = [
    path('generate_token/<int:order_id>', views.generate_token, name='generate_token'),
    path('validate_token', views.validate_token, name='validate_token'),
]
