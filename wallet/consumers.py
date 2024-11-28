import json

from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync

from .models import Wallet, WalletTransaction


class WalletConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.wallet_id = self.scope['url_route']['kwargs']['wallet_uuid']
        self.wallet = get_object_or_404(Wallet, id=self.wallet_id)

        # Đây là 1 hàm không đồng bộ nên cần thừa kế phương thức đồng bộ
        async_to_sync(self.channel_layer.group_add)(
            f'wallet_{self.wallet_id}', self.channel_name
        )

        self.accept()

        event = {
            'type': 'message_handler',
        }
        async_to_sync(self.channel_layer.group_send)(
            f'wallet_{self.wallet_id}', event
        )

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.wallet_id, self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        event = {
            'type': 'message_handler',
        }
        async_to_sync(self.channel_layer.group_send)(
            f'wallet_{self.wallet_id}', event
        )

    def message_handler(self, event):
        wallet = Wallet.objects.get(id=self.wallet_id)
        if wallet:
            self.send(text_data=json.dumps(wallet.to_json()))
        else:
            self.send(text_data='Không tìm thấy giao dịch')

