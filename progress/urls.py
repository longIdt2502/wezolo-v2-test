from django.urls import path
from .views import *


urlpatterns = [
    path('tag_pregress', ProgressApi.as_view()),
    path('detail/<int:pk>', ProgressDetail.as_view()),
]
