from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from .serializers import RegisterSerializer, UserSerializer
from .models import UserProfile

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
