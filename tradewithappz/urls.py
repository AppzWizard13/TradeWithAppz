"""appzone_base URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin 
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from account import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')),
    path('', include('trading_tool.urls')),
    path('', include('fyersapi.urls')),
]

# Static and Media URL patterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# routing.py or urls.py for WebSocket routing
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from fyersapi.routing import ws_urlpatterns  # Import your WebSocket URL patterns

application = ProtocolTypeRouter({
    "websocket": URLRouter(
        ws_urlpatterns
    ),
})