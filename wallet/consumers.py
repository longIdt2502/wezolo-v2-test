import json

from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync

from .models import Wallet, WalletTransaction


class WalletConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.wallet_uuid = self.scope['url_route']['kwargs']['wallet_uuid']
        self.wallet = get_object_or_404(Wallet, id=self.wallet_uuid)

        # Đây là 1 hàm không đồng bộ nên cần thừa kế phương thức đồng bộ
        async_to_sync(self.channel_layer.group_add)(
            f'wallet_{self.wallet_uuid}', self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.wallet_uuid, self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        event = {
            'type': 'message_handler',
            'wallet_trans_id': text_data_json['wallet_transaction']
        }
        async_to_sync(self.channel_layer.group_send)(
            self.wallet_uuid, event
        )

    def message_handler(self, event):
        wallet_trans = WalletTransaction.objects.filter(id=event['wallet_trans_id']).first()
        if wallet_trans:
            self.send(text_data=json.dumps(wallet_trans.to_json()))
        else:
            self.send(text_data='Không tìm thấy giao dịch')

