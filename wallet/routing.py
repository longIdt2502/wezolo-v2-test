from django.urls import path
from .consumers import *

websocket_urlpatterns = [
    path("ws/wallet/<wallet_uuid>", WalletConsumer.as_asgi()),
]

