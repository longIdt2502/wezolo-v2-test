from django.urls import path
from .views import RewardsApi

urlpatterns = [
    path('', RewardsApi.as_view()),
]
