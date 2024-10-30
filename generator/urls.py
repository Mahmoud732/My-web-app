from django.urls import path
from . import views

urlpatterns = [
    path('generate_token/', views.generate_token, name='generate_token'),
]
