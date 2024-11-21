"""
ASGI config for wezolo project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

from wallet import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wezolo.settings')

# Đoạn code này khi khởi tạo ứng dụng, chỉ nhận các yêu cầu HTTP đến
django_asgi_app = get_asgi_application()

# Thêm đoạn code này để có thể khởi tạo bộ định tuyến xử lý websockets
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns))
    )
})
