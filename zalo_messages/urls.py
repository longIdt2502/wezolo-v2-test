from django.urls import path
from .views import *

urlpatterns = [
    path('messages', MessageApi.as_view()),
    path('messages/<str:pk>', MessageListApi.as_view()),
    path('messages/file/<str:pk>', MessageFileListApi.as_view())
]
