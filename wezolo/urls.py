"""wezolo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include('user.urls')),
    path('v1/', include('workspace.urls')),
    path('v1/employee/', include('employee.urls')),
    path('v1/wallet/', include('wallet.urls')),
    path('v1/reward/', include('reward.urls')),
    path('v1/zalo/', include('zalo.urls')),
    path('v1/customer/', include('customer.urls')),
]
