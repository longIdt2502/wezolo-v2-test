from django.urls import path
from .views import *

urlpatterns = [
    path('list', PackageListApi.as_view()),
]