from django.urls import path
from employee import views

urlpatterns = [
    path('', views.Employees.as_view()),
    path('detail/<int:pk>', views.EmployeeDetail.as_view()),
]
