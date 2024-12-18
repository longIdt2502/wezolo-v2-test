import json
from urllib.parse import parse_qs

from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from asgiref.sync import async_to_sync
from rest_framework.authtoken.models import Token

from employee.models import Employee, EmployeeOa, EmployeeUserZalo
from workspace.models import Role
from zalo.models import UserZalo, ZaloOA


class MessageSendConsumer(WebsocketConsumer):
    def connect(self):
        query_params = parse_qs(self.scope['query_string'].decode())
        self.oa_id = query_params.get('oa_id', [None])[0]
        self.user_zalo_id = self.scope['url_route']['kwargs']['user_zalo_id']
        self.user_zalo = get_object_or_404(UserZalo, user_zalo_id=self.user_zalo_id, oa_id=self.oa_id)

        async_to_sync(self.channel_layer.group_add)(
            f'message_{self.user_zalo_id}', self.channel_name
        )

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f'message_{self.user_zalo_id}', self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        event = {
            'type': 'message_handler',
            'message': message
        }
        async_to_sync(self.channel_layer.group_send)(
            f'message_{self.user_zalo_id}', event
        )

    def message_handler(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event['message']))


# This comsumer listen list user_zalo message, who employee take care in Oa
class MessageOaConsumer(WebsocketConsumer):
    def connect(self):
        query_params = parse_qs(self.scope['query_string'].decode())
        self.user_id = query_params.get('user_id', [None])[0]
        self.oa_id = self.scope['url_route']['kwargs']['oa_id']
        self.zalo_oa = get_object_or_404(ZaloOA, uid_zalo_oa=self.oa_id)

        async_to_sync(self.channel_layer.group_add)(
            f'message_user_in_oa_{self.oa_id}', self.channel_name
        )

        # Lấy headers từ request
        # headers = dict(self.scope['headers'])
        # auth_header = headers.get(b'authorization', None)
        self.accept()

        if self.user_id:
            try:
                self.employee = Employee.objects.get(account_id=self.user_id, workspace=self.zalo_oa.company)
                if self.employee.role.code == Role.Code.SALE:
                    EmployeeOa.objects.get(employee=self.employee, oa=self.zalo_oa)
                return
            except:
                self.send_error("Bạn không có quyền truy cập Zalo Oa")
                self.close()
        else:
            self.send_error("yêu cầu user_id")
        self.close()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f'message_user_in_oa_{self.oa_id}', self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        event = {
            'type': 'message_handler',
            'message': message
        }
        async_to_sync(self.channel_layer.group_send)(
            f'message_user_in_oa_{self.oa_id}', event
        )

    def message_handler(self, event):
        if self.employee.role.code == 'SALE':
            id_user = event.get('message').get('id')
            employee_user_zalo = EmployeeUserZalo.objects.filter(customer_id=id_user, employee=self.employee)[:1]
            if not employee_user_zalo:
                return
        # Send message to WebSocket
        self.send(text_data=json.dumps(event['message']))
    
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    def send_error(self, error_message):
        """
        Gửi message lỗi qua WebSocket.
        """
        self.send(text_data=json.dumps({
            "status": "error",
            "error": error_message,
        }))

