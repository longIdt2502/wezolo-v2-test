from django.urls import path
from .views import *

urlpatterns = [
    path('manage', CampaignApi.as_view())
]