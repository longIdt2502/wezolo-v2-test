from django.urls import path
from .views import *


urlpatterns = [
    path('list', BanksApi.as_view())
]
