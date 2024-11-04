from django.urls import path
from . import views


urlpatterns = [
    path('', views.checkout_view, name='Checkout'),
    path('my-orders/', views.user_orders, name='Orders'),
    path('start-payment/<int:order_id>', views.start_payment, name='start_payment'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
]