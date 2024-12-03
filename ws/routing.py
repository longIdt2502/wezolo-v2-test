from django.urls import path
from consumers import wallet_consumer

websocket_urlpatterns = [
    path("ws/wallet/<wallet_uuid>", wallet_consumer.WalletConsumer.as_asgi()),
]

