from django.urls import path
from . import views


urlpatterns = [
    path('', views.cart_view, name='Cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='AddtoCart'),
    path('increment-item/<int:item_id>/', views.increment_item, name='IncrementItem'),
    path('decrement-item/<int:item_id>/', views.decrement_item, name='DecrementItem'),
]