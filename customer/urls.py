from django.urls import path
from .views import *

urlpatterns = [
    path('create', CustomerCreate.as_view()),
    path('list', CustomerList.as_view()),
]