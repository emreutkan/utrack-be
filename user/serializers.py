from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile
from workout.permissions import (
    is_pro_user, is_paid_pro_user, is_trial_user,
    get_pro_days_remaining, get_trial_days_remaining
)

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
    is_pro = serializers.SerializerMethodField()
    is_paid_pro = serializers.SerializerMethodField()
    is_trial = serializers.SerializerMethodField()
    pro_days_remaining = serializers.SerializerMethodField()
    trial_days_remaining = serializers.SerializerMethodField()
    pro_until = serializers.DateTimeField(read_only=True)
    trial_until = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'is_verified', 'gender', 'height', 'weight', 'created_at', 
                  'is_pro', 'is_paid_pro', 'is_trial', 'pro_days_remaining', 'trial_days_remaining',
                  'pro_until', 'trial_until']
        read_only_fields = ['id', 'email', 'is_verified', 'created_at', 'pro_until', 'trial_until']
    
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
    
    def get_is_pro(self, obj):
        """Check if user has active PRO subscription OR trial"""
        return is_pro_user(obj)
    
    def get_is_paid_pro(self, obj):
        """Check if user has active PAID PRO subscription (not trial)"""
        return is_paid_pro_user(obj)
    
    def get_is_trial(self, obj):
        """Check if user has active free trial"""
        return is_trial_user(obj)
    
    def get_pro_days_remaining(self, obj):
        """Get days remaining for PRO subscription (paid only)"""
        return get_pro_days_remaining(obj)
    
    def get_trial_days_remaining(self, obj):
        """Get days remaining for free trial"""
        return get_trial_days_remaining(obj)