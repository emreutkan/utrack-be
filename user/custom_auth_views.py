"""
Custom authentication views with rate limiting.
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from utrack.throttles import LoginRateThrottle


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """
    Login view with rate limiting to prevent brute force attacks.
    """
    throttle_classes = [LoginRateThrottle]  # 5 login attempts per minute


class ThrottledTokenRefreshView(TokenRefreshView):
    """
    Token refresh view with rate limiting.
    """
    throttle_classes = [LoginRateThrottle]  # Same limit as login
