from django.conf import settings
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter

websocket_urlpatterns = []

if settings.GIS_ENABLED:
    from tracking.routing import websocket_urlpatterns as tracking_websocket_urlpatterns

    websocket_urlpatterns = tracking_websocket_urlpatterns


websocket_application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
