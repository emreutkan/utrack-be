from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=False, default='male')
    height = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, help_text="Height in cm")

    class Meta:
        model = User
        fields = ['email', 'password', 'gender', 'height']

    def create(self, validated_data):
        # Get gender and height from validated_data
        gender = validated_data.pop('gender', 'male')
        height = validated_data.pop('height', None)
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            gender=gender
        )
        
        # Set height in UserProfile if provided
        if height is not None:
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.height = height
            profile.save()
        
        return user

class UserSerializer(serializers.ModelSerializer):
    height = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'is_verified', 'gender', 'height', 'weight', 'created_at']
        read_only_fields = ['id', 'email', 'is_verified', 'created_at']
    
    def get_height(self, obj):
        """Get height from UserProfile"""
        try:
            profile = obj.userprofile
            return float(profile.height) if profile.height else None
        except UserProfile.DoesNotExist:
            return None
    
    def get_weight(self, obj):
        """Get latest weight from UserProfile"""
        try:
            profile = obj.userprofile
            return float(profile.body_weight) if profile.body_weight else None
        except UserProfile.DoesNotExist:
            return None