from django.urls import path
from .views import (
    RegisterView, UserProfileView, UpdateHeightView, UpdateGenderView, 
    ChangePasswordView, RequestPasswordResetView, ResetPasswordView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='me'),
    path('height/', UpdateHeightView.as_view(), name='update_height'),
    path('gender/', UpdateGenderView.as_view(), name='update_gender'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('request-password-reset/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
