"""Authentication API URLs."""
from django.urls import path
from .views import (
    LoginView,
    RefreshView,
    LogoutView,
    CSRFView,
    SignupView,
    CountriesView,
    RequestOTPView,
    VerifyOTPView,
    RequestPasswordResetView,
    ResetPasswordView,
)

app_name = "accounts"

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshView.as_view(), name="refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/csrf/", CSRFView.as_view(), name="csrf"),
    path("auth/countries/", CountriesView.as_view(), name="countries"),
    path("auth/request-otp/", RequestOTPView.as_view(), name="request_otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("auth/request-password-reset/", RequestPasswordResetView.as_view(), name="request_password_reset"),
    path("auth/reset-password/", ResetPasswordView.as_view(), name="reset_password"),
]