"""
PRO subscription permission utilities
"""
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone


def require_pro(view_func):
    """
    Decorator to require PRO subscription for a view.
    Returns 403 with upgrade message if user is not PRO.
    """
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required',
                'message': 'Please log in to access this feature'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user has active PRO subscription
        if not is_pro_user(request.user):
            return Response({
                'error': 'PRO feature',
                'message': 'This feature requires PRO subscription',
                'is_pro': False,
                'upgrade_url': '/upgrade'  # Frontend can handle this
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(self, request, *args, **kwargs)
    return wrapper


def is_pro_user(user):
    """
    Check if user has active PRO subscription.
    Returns True if user is PRO and subscription hasn't expired.
    """
    if not user.is_authenticated:
        return False
    
    if not user.is_pro:
        return False
    
    # Check if PRO subscription has expired
    if user.pro_until and timezone.now() > user.pro_until:
        # Subscription expired, update user
        user.is_pro = False
        user.save(update_fields=['is_pro'])
        return False
    
    return True


def get_pro_response():
    """
    Returns standard PRO upgrade response.
    """
    return Response({
        'error': 'PRO feature',
        'message': 'This feature requires PRO subscription',
        'is_pro': False,
        'upgrade_url': '/upgrade'
    }, status=status.HTTP_403_FORBIDDEN)





