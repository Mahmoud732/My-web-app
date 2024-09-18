from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views


urlpatterns = [
    path('product', views.product, name='product'),
    path('', views.products, name='products'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)