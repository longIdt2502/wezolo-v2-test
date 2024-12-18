from django.urls import path
from ws.consumers import wallet_consumer, sync_oa_connect_consumer, message_send_consumer

websocket_urlpatterns = [
    path("ws/wallet/<wallet_uuid>", wallet_consumer.WalletConsumer.as_asgi()),
    path("ws/sync_oa_connect/<oa_id>", sync_oa_connect_consumer.SyncOaConnectConsumer.as_asgi()),
    path("ws/message_zalo/<user_zalo_id>", message_send_consumer.MessageSendConsumer.as_asgi()),
    path("ws/message_zalo_oa/<oa_id>", message_send_consumer.MessageOaConsumer.as_asgi()),
]

