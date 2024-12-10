from django.urls import path
from .views import *


urlpatterns = [
    path('tag', TagsApi.as_view()),
    path('detail/<int:pk>', TagDetail.as_view()),
]
