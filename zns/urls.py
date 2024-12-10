from django.urls import path
from .views import *

urlpatterns = [
    path('create', ZnsCreateApi.as_view()),
    path('list', ZnsApi.as_view())
]