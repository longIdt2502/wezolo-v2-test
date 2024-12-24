from django.urls import path
from .views import *

urlpatterns = [
    path('create', ZnsCreateApi.as_view()),
    path('list', ZnsApi.as_view()),
    path('detail/<int:pk>', ZnsDetail.as_view()),
    path('list-price', ZnsTypePrice.as_view()),
    path('send', MessageOpenApi.as_view()),
    path('send-v2', MessageOpenApiV2.as_view()),
]
