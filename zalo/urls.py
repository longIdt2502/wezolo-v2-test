from django.urls import path
from zalo.views.views import *
from zalo.admins.views import *
from zalo.views.zalo_user_views import *
from zalo.hook.views import *

urlpatterns = [
    path('zalo_oa', ZaloOaAPI.as_view()),
    path('zalo_oa/<int:pk>', ZaloOaDetailAPI.as_view()),
    path('zalo_oa_url_connection', ZaloOaUrlConnection.as_view()),
    path('zalo_oa_accept_auth/hook/<int:pk>', ZaloOaAcceptAuth.as_view()),
    path('hook', ZaloHook.as_view()),

    path('zalo_user/create', ZaloUserCreate.as_view()),
    path('zalo_user/send_sync_process', ZaloUserSendSyncProcess.as_view()),
    path('zalo_user/list', ZaloUserList.as_view()),
    path('zalo_message/create_multi', ZaloMessageCreate.as_view()),

    path('admin/list', ZaloAdminList.as_view()),
    path('admin/oa/<int:pk>', ZaloAdminActionOa.as_view())
]
