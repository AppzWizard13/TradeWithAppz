# routing.py

from django.urls import path
from .consumers import  FyersPositionDataConsumer, FyersIndexDataConsumer
from django.urls import path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

ws_urlpatterns = [
    path('ws/fyersindexdata/<str:last_keyword>/', FyersIndexDataConsumer.as_asgi()),
    path('ws/fyerspositionsdata/', FyersPositionDataConsumer.as_asgi()),


    
]

application = ProtocolTypeRouter(
    {
        "websocket": AuthMiddlewareStack(
            URLRouter(ws_urlpatterns)
        ),
    }
)
