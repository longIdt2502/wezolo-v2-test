from django.db import models

from user.models import User
from zalo.models import ZaloOA


class Chatbot(models.Model):
    class Meta:
        verbose_name = 'Chatbot'
        db_table = 'chatbot'

    name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False)
    oa = models.ForeignKey(ZaloOA, on_delete=models.CASCADE, null=False)
    index = models.IntegerField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='user_create_campaign')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_update_campaign')


class ChatbotAnswer(models.Model):
    class Meta:
        verbose_name = 'ChatbotAnswer'
        db_table = 'chatbot_answer'

    class Type(models.TextChoices):
        GREETING = 'GREETING', 'Lời chào ban đầu'
        SPECIFIC = 'SPECIFIC', 'Theo kịch bản hỏi'
        NOT_FOUND = 'NOT_FOUND', 'Không có câu hỏi'
        FAREWELL = 'FAREWELL', 'Kết thúc trò chuyện'
        HELP = 'HELP', 'Câu hướng dẫn'

    answer = models.TextField(null=False)
    chatbot = models.ForeignKey(Chatbot, on_delete=models.SET_NULL, null=True)
    image = models.CharField(max_length=255, null=True, blank=True)
    type = models.CharField(max_length=60, choices=Type.choices, null=True)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='user_create_answer')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_update_answer')


class ChatbotQuestion(models.Model):
    class Meta:
        verbose_name = 'ChatbotQuestion'
        db_table = 'chatbot_question'

    class Type(models.TextChoices):
        KEYWORD = 'KEYWORD'
        QUESTION = 'QUESTION'

    content = models.TextField(null=False)
    type = models.CharField(max_length=60, choices=Type.choices, null=True)
    answer = models.ForeignKey(ChatbotAnswer, on_delete=models.CASCADE, null=False)
    create_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=False, related_name='user_create_question')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_update_question')
