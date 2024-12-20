from django.urls import path
from .views import *

urlpatterns = [
    path('messages', MessageApi.as_view()),
    path('messages/func/request-info', MessageRequestInfoApi.as_view()),
    path('messages/<str:pk>', MessageListApi.as_view()),
    path('messages/file/<str:pk>', MessageFileListApi.as_view()),
    path('messages/file/upload/zalo', MessageFileUploadApi.as_view()),
    path('messages/sticker/list', MessageStickerApi.as_view()),
    path('messages/sticker/detail/<str:pk>', MessageStickerDetailApi.as_view()),
]
