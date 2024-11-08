from django.urls import path
from . import views

urlpatterns = [
    path('shop', views.products_view, name='Shop'),
    path('product/<int:product_id>', views.product_view, name='product'),
]