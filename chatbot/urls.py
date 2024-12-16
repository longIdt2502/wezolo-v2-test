from django.urls import path
from .views import *

urlpatterns = [
    path('manage', ChatbotApi.as_view()),
    path('detail/<int:pk>', ChatbotDetail.as_view()),
]
