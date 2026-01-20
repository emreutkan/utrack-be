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
    Check if user has active PRO subscription OR free trial.
    Returns True if user is PRO (paid) or has active trial.
    """
    if not user.is_authenticated:
        return False
    
    # Check free trial first
    if user.trial_until and timezone.now() <= user.trial_until:
        return True
    
    # Check paid PRO subscription
    if not user.is_pro:
        return False
    
    # Check if PRO subscription has expired
    if user.pro_until and timezone.now() > user.pro_until:
        # Subscription expired, update user
        user.is_pro = False
        user.save(update_fields=['is_pro'])
        return False
    
    return True


def is_paid_pro_user(user):
    """
    Check if user has active PAID PRO subscription (not trial).
    Returns True only if user has paid subscription.
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


def is_trial_user(user):
    """
    Check if user has active free trial.
    Returns True if user has active trial (even if expired).
    """
    if not user.is_authenticated:
        return False
    
    if not user.trial_until:
        return False
    
    # Check if trial has expired
    if timezone.now() > user.trial_until:
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


def get_pro_days_remaining(user):
    """
    Calculate days remaining for PRO subscription (paid only).
    Returns:
    - int: Days remaining (0 if expired or no subscription)
    - None: If user doesn't have a pro_until date set
    """
    if not user.is_authenticated:
        return None
    
    if not user.pro_until:
        return None
    
    now = timezone.now()
    
    # If already expired, return 0
    if now > user.pro_until:
        return 0
    
    # Calculate days remaining
    delta = user.pro_until - now
    days_remaining = delta.days
    
    # If less than 1 day but still in future, return 0 (will expire today)
    if days_remaining < 0:
        return 0
    
    return days_remaining


def get_trial_days_remaining(user):
    """
    Calculate days remaining for free trial.
    Returns:
    - int: Days remaining (0 if expired or no trial)
    - None: If user doesn't have a trial_until date set
    """
    if not user.is_authenticated:
        return None
    
    if not user.trial_until:
        return None
    
    now = timezone.now()
    
    # If already expired, return 0
    if now > user.trial_until:
        return 0
    
    # Calculate days remaining
    delta = user.trial_until - now
    days_remaining = delta.days
    
    # If less than 1 day but still in future, return 0 (will expire today)
    if days_remaining < 0:
        return 0
    
    return days_remaining





