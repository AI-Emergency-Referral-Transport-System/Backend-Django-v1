import os
from pathlib import Path

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from dotenv import load_dotenv
import tracking.routing


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "config.settings"),

django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter(
    {
        # Handle traditional HTTP requests
    "http": get_asgi_application(),

    # Handle WebSocket requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            tracking.routing.websocket_urlpatterns
        )
    ),
    }
)
