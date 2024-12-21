from django.urls import path
from .views import *

urlpatterns = [
    path('detail', RewardsApi.as_view()),
    path('list', RewardsTierApi.as_view()),
]
