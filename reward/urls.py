from django.urls import path
from .views import *

urlpatterns = [
    path('', RewardsApi.as_view()),
    path('list', RewardsTierApi.as_view()),
]
