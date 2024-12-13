from django.urls import path
from .views import *

urlpatterns = [
    path('campaign', ChatbotApi.as_view())
]
