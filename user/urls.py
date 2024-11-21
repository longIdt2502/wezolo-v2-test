from django.urls import path
from user import views

urlpatterns = [
    path('users/login', views.LoginView.as_view()),
    path('users/register', views.RegisterView.as_view()),
    path('users/profile', views.ProfileView.as_view()),
    path('users/forgot_password', views.ForgotPasswordAPIView.as_view()),
    path('users/forgot_password_verify', views.ForgotPasswordConfirmOTPAPIView.as_view()),
    path('users/change_password', views.SetNewPasswordAPIView.as_view()),
    path('verify', views.VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('send-code', views.ResendOTPAPIView.as_view(), name='resend-otp'),
    # path('generate-qr', views.GenerateQRForAccount.as_view(), name='generate-otp'),
    path("cities", views.CityListAPIView.as_view()),
    path("districts", views.DistrictListAPIView.as_view()),
    path("wards", views.WardListAPIView.as_view()),
]
