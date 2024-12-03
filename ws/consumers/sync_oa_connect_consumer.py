import json

from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync

from zalo.models import ZaloOA


class SyncOaConnectConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.oa_id = self.scope['url_route']['kwargs']['oa_id']
        self.oa = get_object_or_404(ZaloOA, id=self.oa_id)

        # Đây là 1 hàm không đồng bộ nên cần thừa kế phương thức đồng bộ
        async_to_sync(self.channel_layer.group_add)(
            f'oa_{self.oa_id}', self.channel_name
        )

        self.accept()

        event = {
            'type': 'message_handler',
            'message': {
                'sync_done': 0,
                'total_sync': 100
            }
        }
        async_to_sync(self.channel_layer.group_send)(
            f'oa_{self.oa_id}', event
        )

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f'oa_{self.oa_id}', self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        event = {
            'type': 'message_handler',
            'message': message
        }
        async_to_sync(self.channel_layer.group_send)(
            f'oa_{self.oa_id}', event
        )

    def message_handler(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event['message']))

