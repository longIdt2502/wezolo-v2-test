from django.urls import path
from .views import *

urlpatterns = [
    path('detail/<uuid:pk>', WalletDetail.as_view()),
    path('payment', WalletPayment.as_view()),
    path('transaction', WalletTransApi.as_view()),
    path('admin/transaction-by-user/<int:pk>', WalletTransAdminApi.as_view()),
    path('receive-hook-payment', WalletReceiveHookPayment.as_view()),
]
