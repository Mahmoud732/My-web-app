from django.urls import path
from . import views


urlpatterns = [
    path('', views.checkout_view, name='Checkout'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.user_orders, name='Orders'),

]