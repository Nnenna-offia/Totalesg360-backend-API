"""Authentication API URLs."""
from django.urls import path
from .views import LoginView, RefreshView, LogoutView, CSRFView, SignupView, CountriesView

app_name = "accounts"

urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshView.as_view(), name="refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/csrf/", CSRFView.as_view(), name="csrf"),
    path("auth/countries/", CountriesView.as_view(), name="countries"),
]