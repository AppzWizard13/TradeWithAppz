"""
ASGI config for tradewithappz project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from fyersapi.routing import ws_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tradewithappz.settings')

# Regular Django ASGI application
django_asgi_application = get_asgi_application()

# Django Channels WebSocket application
application = ProtocolTypeRouter(
    {
        "https": django_asgi_application,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                ws_urlpatterns
            )
        ),
    }
)