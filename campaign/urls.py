from django.urls import path
from .views import *

urlpatterns = [
    path('manage', CampaignApi.as_view()),
    path('detail/<int:pk>', CampaignDetailApi.as_view()),
    path('detail/list-message/<int:pk>', CampaignListMessageApi.as_view()),
    # path('message/<int:pk>', CampaignApi.as_view()),
    path('zns/<int:pk>', CampaignZnsDetailApi.as_view())
]