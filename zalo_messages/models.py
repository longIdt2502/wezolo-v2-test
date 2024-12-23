from datetime import datetime
import json
from django.db import models
from wheel.metadata import _
from chatbot.models import Chatbot, ChatbotAnswer, ChatbotQuestion
from common.core.subquery import SubqueryJsonAgg
from employee.models import EmployeeUserZalo
from tags.models import TagUserZalo
import pytz

from user.models import User
from ws.event import send_message_to_ws
from zalo.models import UserZalo, ZaloOA
from zalo_messages.utils import send_message_text


class Message(models.Model):
    class Meta:
        verbose_name = "Message"
        db_table = "message"

    class Src(models.IntegerChoices):
        OA = 0, 'OA'
        USER = 1, 'USER'

    class Type(models.TextChoices):
        TEXT = 'TEXT', 'tin nhắn văn bản'
        VOICE = 'VOICE', 'tin nhắn thoại'
        PHOTO = 'PHOTO', 'tin nhắn ảnh'
        VIDEO = 'VIDEO', 'tin nhắn video'
        GIFT = 'GIFT', 'tin nhắn GIFT'
        LINK = 'LINK', 'tin nhắn có nội dung là đường link'
        LINKS = 'LINKS', 'tin nhắn theo mẫu đính kèm danh sách'
        STICKER = 'STICKER', 'tin nhắn sticker'
        LOCATION = 'LOCATION', 'tin nhắn chia sẻ location'
        BUSINESS_CARD = 'BUSINESS_CARD', 'người dùng gửi danh thiếp'
        FILE = 'FILE', 'tin nhắn file'

    class TypeSend(models.TextChoices):
        USER = 'USER', 'Người dùng gửi'
        CAMPAIGN = 'CAMPAIGN', 'Chiến dịch gửi'
        BOT = 'BOT', 'Bot gửi'
    
    class Status(models.TextChoices):
        SENDING = 'SENDING', 'Đang gửi'
        SENT = 'SENT', 'Đã gửi'
        RECEIVED = 'RECEIVED', 'Đã nhận'
        SEEN = 'SEEN', 'Đã xem'

    message_id = models.CharField(max_length=255, null=True, blank=True)
    quote_msg_id = models.CharField(max_length=255, null=True, blank=True)
    uuid = models.UUIDField(null=True)
    src = models.IntegerField(choices=Src.choices, null=True, blank=True)
    send_at = models.FloatField(null=True)
    type_message = models.CharField(max_length=255, choices=Type.choices, null=False, default=Type.TEXT)
    type_send = models.CharField(max_length=255, null=True, choices=TypeSend.choices)
    message_text = models.TextField(null=True)
    message_thumb = models.TextField(null=True)
    message_url = models.TextField(null=True)
    message_links = models.TextField(null=True)
    message_location = models.TextField(null=True)
    message_description_photo = models.TextField(null=True)
    from_id = models.CharField(max_length=255, null=False, blank=False)
    to_id = models.CharField(max_length=255, null=False, blank=False)
    success = models.BooleanField(null=True)
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.SENDING, null=True)
    read_at = models.DateTimeField(null=True)
    send_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL, null=True, related_name='oa_message')

    def save(self, *args, **kwargs):

        if self.src == Message.Src.OA:
            answer = ChatbotAnswer.objects.filter(answer=self.message_text).first()
            if answer:
                self.type_send = Message.TypeSend.BOT

        super().save(*args, **kwargs)

        # Send message to socket thread detail chat
        user_zalo_id = self.from_id if self.src == Message.Src.USER else self.to_id
        send_message_to_ws(f'message_{user_zalo_id}', 'message_handler', self.to_json())

        # Send message to socket thread OA
        user_zalo = UserZalo.objects.filter(user_zalo_id=user_zalo_id).first()
        if self.src == Message.Src.USER:
            user_zalo.message_unread += 1
        else:
            user_zalo.message_unread = 0
        user_zalo.last_message_time = datetime.fromtimestamp(float(self.send_at) / 1000).astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
        user_zalo.save()
        send_message_to_ws(f'message_user_in_oa_{self.oa.uid_zalo_oa}', 'message_handler', user_zalo.to_json())

        if self.src == Message.Src.USER:
            if user_zalo.chatbot:
                # Kiểm tra xem có chat bot nào hoạt động không
                chatbot = Chatbot.objects.filter(is_active=True, oa=user_zalo.oa).first()
                # Nếu có thực hiện các func liên quan
                if chatbot:
                    last_message_oa_send = Message.objects.filter(src=Message.Src.OA).last()
                    answer = None
                    """
                    Kiểm tra tin nhắn cuối mà OA gửi cho khách
                    - Nếu là tin nhắn BOT thì thực hiện tìm kiếm các câu hỏi và câu trả lời
                    - Nếu ko là tin nhắn BOT thì sẽ thực hiện câu trả lời chào mừng
                    """
                    if last_message_oa_send.type_send != self.TypeSend.BOT:
                        answer = ChatbotAnswer.objects.filter(type=ChatbotAnswer.Type.GREETING, chatbot=chatbot).first()
                    else:
                        # Tìm các câu hỏi có câu trả lời nằm trong Chatbot đang hoạt động
                        list_question = ChatbotQuestion.objects.filter(
                            answer__chatbot=chatbot
                        )
                        # Tìm câu hỏi có keyword nằm trong tin nhắn của khách
                        for item in list_question:
                            if answer:
                                continue
                            if item.type == ChatbotQuestion.Type.KEYWORD:
                                keywords = item.content.split(',')
                                for key in keywords:
                                    if key.lower() in self.message_text.lower():
                                        answer = item.answer
                        # Nếu ko có trả lời phù hợp thì chọn câu trả lời not found
                        if not answer:
                            answer = ChatbotAnswer.objects.filter(type=ChatbotAnswer.Type.NOT_FOUND, chatbot=chatbot).first()
                    send_message_text(user_zalo.oa, user_zalo_id, {
                        'text': answer.answer,
                    })

    def from_json(self, data):
        message = Message.objects.create(
            message_id=data.get('message_id'),
            quote_msg_id=data.get('quote_msg_id'),
            src=data.get('src'),
            send_at=data.get('send_at', int(datetime.now().timestamp() * 1000)),
            type_message=data.get('type_message'),
            type_send=data.get('type_send'),
            message_text=data.get('message_text'),
            message_url=data.get('message_url'),
            message_links=data.get('message_links'),
            message_location=data.get('message_location'),
            from_id=data.get('from_id'),
            to_id=data.get('to_id'),
            success=data.get('success'),
            oa_id=data.get('oa'),
        )
        return message

    def to_json(self):
        user_zalo = UserZalo.objects.filter(models.Q(user_zalo_id=self.from_id) | models.Q(user_zalo_id=self.to_id)).values(
            'phone', 'user_zalo_id', 'avatar_small', 'avatar_big', 'message_quota_type', 'message_remain', 'message_quota'
        ).first()
        if user_zalo:
            user_zalo = json.dumps(user_zalo)
        else:
            user_zalo = None
        return {
            'id': self.id,
            'message_id': self.message_id,
            'quote_msg_id': self.quote_msg_id,
            'uuid': self.uuid,
            'message_text': self.message_text,
            'message_url': self.message_url,
            'message_links': self.message_links,
            'message_location': self.message_location,
            'from_id': self.from_id,
            'to_id': self.to_id,
            'success': self.success,
            'read_at': self.read_at.strftime('%Y-%m-%d %H:%M:%S') if self.read_at else None,
            'send_at': self.send_at,
            'type_message': self.type_message,
            'type_send': self.type_send,
            'status': self.status,
            'src': self.src,
            'oa': self.oa.to_json() if self.oa else None,
            'user_zalo': user_zalo
        }