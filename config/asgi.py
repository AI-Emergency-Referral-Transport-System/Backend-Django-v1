import os
from pathlib import Path

from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "config.settings"),

django_asgi_app = get_asgi_application()

websocket_urlpatterns = []
if settings.GIS_ENABLED:
    from tracking.routing import websocket_urlpatterns as tracking_websocket_urlpatterns

    websocket_urlpatterns = tracking_websocket_urlpatterns


application = ProtocolTypeRouter(
    {
        # Handle traditional HTTP requests
    "http": get_asgi_application(),

    # Handle WebSocket requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
    }
)
