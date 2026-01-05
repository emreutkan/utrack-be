from django.urls import path
from .views import (
    RegisterView, UserProfileView, UpdateHeightView, UpdateGenderView, 
    ChangePasswordView, RequestPasswordResetView, ResetPasswordView,
    UpdateWeightView, GetWeightHistoryView, DeleteWeightView,
    CheckEmailView, CheckPasswordView, CheckNameView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserProfileView.as_view(), name='me'),
    path('height/', UpdateHeightView.as_view(), name='update_height'),
    path('weight/', UpdateWeightView.as_view(), name='update_weight'),
    path('weight/history/', GetWeightHistoryView.as_view(), name='get_weight_history'),
    path('weight/<int:weight_id>/', DeleteWeightView.as_view(), name='delete_weight'),
    path('gender/', UpdateGenderView.as_view(), name='update_gender'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('request-password-reset/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('check-email/', CheckEmailView.as_view(), name='check_email'),
    path('check-password/', CheckPasswordView.as_view(), name='check_password'),
    path('check-name/', CheckNameView.as_view(), name='check_name'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
