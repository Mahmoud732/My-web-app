from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('registration.urls')),
    path('', include('app.urls')),
    path('', include('product.urls')),
    path('cart/', include('cart.urls')),
    path('checkout/', include('checkout.urls')),
    path('generator/', include('generator.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
