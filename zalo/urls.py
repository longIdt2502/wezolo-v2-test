from django.urls import path
from .views import *

urlpatterns = [
    path('zalo_oa', ZaloOaAPI.as_view()),
    path('zalo_oa/<int:pk>', ZaloOaDetailAPI.as_view()),
    path('zalo_oa_url_connection', ZaloOaUrlConnection.as_view()),
    path('zalo_oa_accept_auth/hook/<int:pk>', ZaloOaAcceptAuth.as_view()),

    path('zalo_user/create', ZaloUserCreate.as_view()),
    path('zalo_message/create_multi', ZaloMessageCreate.as_view()),
]
