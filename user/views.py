from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .serializers import RegisterSerializer, UserSerializer
from .models import UserProfile, WeightHistory
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from datetime import date
from body_measurements.models import BodyMeasurement
import re
import html

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def patch(self, request):
        """
        PATCH /api/user/me/
        Update user profile (currently supports gender update)
        """
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateHeightView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/user/height/
        Set or update user's height (in cm)
        """
        height = request.data.get('height')
        
        if height is None:
            return Response({
                'error': 'height field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            height = float(height)
            if height <= 0:
                return Response({
                    'error': 'height must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': 'height must be a valid number'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.height = height
        profile.save()
        
        return Response({
            'height': str(profile.height),
            'message': 'Height updated successfully'
        }, status=status.HTTP_200_OK)

class UpdateGenderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/user/gender/
        Update user's gender
        """
        gender = request.data.get('gender')
        
        if gender is None:
            return Response({
                'error': 'gender field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if gender not in ['male', 'female']:
            return Response({
                'error': 'gender must be either "male" or "female"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.gender = gender
        request.user.save()
        
        return Response({
            'gender': request.user.gender,
            'message': 'Gender updated successfully'
        }, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/user/change-password/
        Change user's password
        Requires: old_password, new_password
        """
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({
                'error': 'old_password and new_password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify old password
        if not request.user.check_password(old_password):
            return Response({
                'error': 'Invalid old password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        if len(new_password) < 8:
            return Response({
                'error': 'New password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/user/request-password-reset/
        Request password reset - generates token for password reset
        Requires: email
        Returns: success message (token should be sent via email in production)
        """
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'email field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            return Response({
                'message': 'If an account with this email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate token and uid
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # TODO: Send email with reset link here
        # In production, send email with reset link instead of returning token
        # For security, don't return token in response
        
        return Response({
            'message': 'If an account with this email exists, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/user/reset-password/
        Reset password using token
        Requires: uid, token, new_password
        """
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not uid or not token or not new_password:
            return Response({
                'error': 'uid, token, and new_password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        if len(new_password) < 8:
            return Response({
                'error': 'New password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Decode uid to get user pk
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token
        if not default_token_generator.check_token(user, token):
            return Response({
                'error': 'Invalid or expired reset token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)

class UpdateWeightView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        POST /api/user/weight/
        Set or update user's current weight (in kg)
        Creates a new weight history entry and updates UserProfile.body_weight
        """
        weight = request.data.get('weight')
        
        if weight is None:
            return Response({
                'error': 'weight field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            weight = float(weight)
            if weight <= 0:
                return Response({
                    'error': 'weight must be greater than 0'
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': 'weight must be a valid number'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new weight history entry
        weight_entry = WeightHistory.objects.create(
            user=request.user,
            weight=weight
        )
        
        # Update UserProfile with latest weight
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.body_weight = weight
        profile.save()
        
        return Response({
            'weight': str(weight_entry.weight),
            'date': weight_entry.created_at.isoformat(),
            'message': 'Weight updated successfully'
        }, status=status.HTTP_200_OK)

class WeightHistoryPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

class GetWeightHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = WeightHistoryPagination
    
    def get(self, request):
        """
        GET /api/user/weight/
        Get paginated weight history for the user (100 per page)
        Returns: date, weight, bodyfat (if body measurement exists for that day)
        """
        paginator = WeightHistoryPagination()
        
        # Get all weight history entries for the user
        weight_history = WeightHistory.objects.filter(user=request.user).order_by('-created_at')
        
        # Paginate - always returns paginated results
        page = paginator.paginate_queryset(weight_history, request)
        
        results = []
        for entry in page:
            # Get date (just the date part, not time)
            entry_date = entry.created_at.date()
            
            # Try to find body measurement on the same date
            body_fat = None
            body_measurement = BodyMeasurement.objects.filter(
                user=request.user,
                created_at__date=entry_date
            ).first()
            
            if body_measurement and body_measurement.body_fat_percentage:
                body_fat = float(body_measurement.body_fat_percentage)
            
            results.append({
                'id': entry.id,
                'date': entry.created_at.isoformat(),
                'weight': float(entry.weight),
                'bodyfat': body_fat
            })
        
        return paginator.get_paginated_response(results)

class DeleteWeightView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, weight_id):
        """
        DELETE /api/user/weight/<weight_id>/
        Delete a weight history entry.
        Optional query parameter: delete_bodyfat=true to also delete body measurements on the same date
        """
        try:
            # Get the weight history entry
            weight_entry = WeightHistory.objects.get(
                id=weight_id,
                user=request.user
            )
        except WeightHistory.DoesNotExist:
            return Response({
                'error': 'Weight entry not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the date of the weight entry
        entry_date = weight_entry.created_at.date()
        
        # Check if user wants to delete bodyfat on the same date
        delete_bodyfat = request.query_params.get('delete_bodyfat', 'false').lower() == 'true'
        
        deleted_bodyfat = False
        if delete_bodyfat:
            # Find and delete body measurements on the same date
            body_measurements = BodyMeasurement.objects.filter(
                user=request.user,
                created_at__date=entry_date
            )
            if body_measurements.exists():
                count = body_measurements.count()
                body_measurements.delete()
                deleted_bodyfat = True
        
        # Delete the weight entry
        weight_entry.delete()
        
        # Update UserProfile.body_weight to latest weight if this was the latest entry
        latest_weight = WeightHistory.objects.filter(user=request.user).order_by('-created_at').first()
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if latest_weight:
            profile.body_weight = latest_weight.weight
        else:
            profile.body_weight = None
        profile.save()
        
        response_data = {
            'message': 'Weight entry deleted successfully',
            'deleted_date': entry_date.isoformat()
        }
        
        if delete_bodyfat:
            response_data['bodyfat_deleted'] = deleted_bodyfat
        
        return Response(response_data, status=status.HTTP_200_OK)


def check_xss_injection(text):
    """
    Check for XSS and injection patterns in text.
    Returns list of detected threats.
    """
    threats = []
    
    if not text:
        return threats
    
    # XSS patterns
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<img[^>]*src\s*=\s*["\']javascript:',
        r'<svg[^>]*onload',
        r'expression\s*\(',
        r'vbscript:',
        r'data:text/html',
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            threats.append('XSS')
            break
    
    # SQL injection patterns
    sql_patterns = [
        r"('|(\\')|(;)|(\\;)|(--)|(\\--)|(/\*)|(\\/\*)|(\*/)|(\\\*/)|(xp_)|(sp_))",
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION)\b)",
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            threats.append('SQL_INJECTION')
            break
    
    # HTML/script tags
    if re.search(r'<[^>]+>', text):
        threats.append('HTML_TAGS')
    
    return threats


def check_email_security(email):
    """
    Check email for security issues.
    Returns list of security threats found.
    """
    threats = []
    
    if not email:
        return threats
    
    # Check for XSS/injection
    xss_threats = check_xss_injection(email)
    threats.extend(xss_threats)
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'[<>]',  # Angle brackets
        r'javascript:',
        r'data:',
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            threats.append('SUSPICIOUS_CHARACTERS')
            break
    
    return threats


def validate_password_strength(password):
    """
    Validate password strength.
    Returns dict with is_valid, errors, and strength_score.
    """
    errors = []
    strength_score = 0
    
    if not password:
        return {
            'is_valid': False,
            'errors': ['Password is required'],
            'strength_score': 0
        }
    
    # Length check
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    else:
        strength_score += 1
    
    if len(password) >= 12:
        strength_score += 1
    
    # Character variety checks
    if re.search(r'[a-z]', password):
        strength_score += 1
    else:
        errors.append('Password should contain at least one lowercase letter')
    
    if re.search(r'[A-Z]', password):
        strength_score += 1
    else:
        errors.append('Password should contain at least one uppercase letter')
    
    if re.search(r'\d', password):
        strength_score += 1
    else:
        errors.append('Password should contain at least one number')
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        strength_score += 1
    else:
        errors.append('Password should contain at least one special character')
    
    # Common weak passwords
    weak_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123']
    if password.lower() in weak_passwords:
        errors.append('Password is too common')
        strength_score = 0
    
    # Security checks
    security_threats = check_xss_injection(password)
    
    return {
        'is_valid': len(errors) == 0 and len(security_threats) == 0,
        'errors': errors,
        'security_threats': security_threats,
        'strength_score': min(strength_score, 5),  # Max score 5
        'strength_level': 'weak' if strength_score < 3 else 'medium' if strength_score < 4 else 'strong'
    }


def validate_name(name):
    """
    Validate name format and security.
    Returns dict with is_valid, errors, and security_threats.
    """
    errors = []
    
    if not name:
        return {
            'is_valid': False,
            'errors': ['Name is required'],
            'security_threats': []
        }
    
    # Length check
    if len(name) < 2:
        errors.append('Name must be at least 2 characters long')
    
    if len(name) > 100:
        errors.append('Name must be less than 100 characters')
    
    # Character check - allow letters, spaces, hyphens, apostrophes
    if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name):
        errors.append('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
    
    # Security checks
    security_threats = check_xss_injection(name)
    
    return {
        'is_valid': len(errors) == 0 and len(security_threats) == 0,
        'errors': errors,
        'security_threats': security_threats
    }


class CheckEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/user/check-email/
        Check if email is valid, available, and secure.
        Body: {"email": "user@example.com"}
        """
        email = request.data.get('email', '').strip()
        
        if not email:
            return Response({
                'is_valid': False,
                'errors': ['Email is required'],
                'user_exists': False,
                'security_threats': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        errors = []
        security_threats = []
        
        # Email format validation
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            errors.append('Invalid email format')
        
        # Normalize email (Django's way)
        try:
            normalized_email = User.objects.normalize_email(email)
        except Exception:
            normalized_email = email.lower().strip()
        
        # Check if user exists
        user_exists = User.objects.filter(email=normalized_email).exists()
        
        # Security checks
        security_threats = check_email_security(email)
        
        # Additional validation
        if len(email) > 254:  # RFC 5321 limit
            errors.append('Email is too long (max 254 characters)')
        
        is_valid = len(errors) == 0 and len(security_threats) == 0
        
        return Response({
            'is_valid': is_valid,
            'errors': errors,
            'user_exists': user_exists,
            'security_threats': security_threats,
            'normalized_email': normalized_email if is_valid else None
        }, status=status.HTTP_200_OK)


class CheckPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/user/check-password/
        Check if password is valid and secure.
        Body: {"password": "mypassword123"}
        """
        password = request.data.get('password', '')
        
        if not password:
            return Response({
                'is_valid': False,
                'errors': ['Password is required'],
                'security_threats': [],
                'strength_score': 0,
                'strength_level': 'weak'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validation_result = validate_password_strength(password)
        
        return Response({
            'is_valid': validation_result['is_valid'],
            'errors': validation_result['errors'],
            'security_threats': validation_result.get('security_threats', []),
            'strength_score': validation_result['strength_score'],
            'strength_level': validation_result['strength_level']
        }, status=status.HTTP_200_OK)


class CheckNameView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/user/check-name/
        Check if name is valid and secure.
        Body: {"name": "John Doe"}
        """
        name = request.data.get('name', '').strip()
        
        if not name:
            return Response({
                'is_valid': False,
                'errors': ['Name is required'],
                'security_threats': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validation_result = validate_name(name)
        
        return Response({
            'is_valid': validation_result['is_valid'],
            'errors': validation_result['errors'],
            'security_threats': validation_result['security_threats']
        }, status=status.HTTP_200_OK)
