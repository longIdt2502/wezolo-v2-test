from django.db import models
from wheel.metadata import _

from user.models import User
from zalo.models import ZaloOA


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
        GIFT = 'GIFT', 'tin nhắn GIFT'
        LINK = 'LINK', 'tin nhắn có nội dung là đường link'
        LINKS = 'LINKS', 'tin nhắn theo mẫu đính kèm danh sách'
        STICKER = 'STICKER', 'tin nhắn sticker'
        LOCATION = 'LOCATION', 'tin nhắn chia sẻ location'

    class TypeSend(models.TextChoices):
        USER = 'USER', 'Người dùng gửi'
        CAMPAIGN = 'CAMPAIGN', 'Chiến dịch gửi'
        BOT = 'BOT', 'Bot gửi'

    message_id = models.CharField(max_length=255, null=True, blank=True)
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
    send_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    oa = models.ForeignKey(ZaloOA, on_delete=models.SET_NULL, null=True, related_name='oa_message')
