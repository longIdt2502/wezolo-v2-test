from django.urls import path
from .views import *

urlpatterns = [
    path('messages', MessageApi.as_view())
]
