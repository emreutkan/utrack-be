from rest_framework import serializers
from .models import Supplement, UserSupplement, UserSupplementLog
from django.utils import timezone
from datetime import date, time

class SupplementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplement
        fields = ['id', 'name', 'description', 'dosage_unit', 'default_dosage', 'bioavailability_score']

class UserSupplementSerializer(serializers.ModelSerializer):
    supplement_details = SupplementSerializer(source='supplement', read_only=True)
    supplement_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplement.objects.all(), source='supplement', write_only=True
    )

    class Meta:
        model = UserSupplement
        fields = [
            'id', 
            'supplement_id', 
            'supplement_details', 
            'dosage', 
            'frequency', 
            'time_of_day', 
            'is_active',
            
        ]
    
    def validate_dosage(self, value):
        """Validate dosage is positive and within reasonable range."""
        if value <= 0:
            raise serializers.ValidationError("Dosage must be greater than 0.")
        if value > 10000:  # Reasonable upper limit (e.g., 10g for creatine)
            raise serializers.ValidationError("Dosage is too high. Please check your input.")
        return value
    
    def validate_frequency(self, value):
        """Validate frequency choice."""
        valid_frequencies = ['daily', 'weekly', 'custom']
        if value not in valid_frequencies:
            raise serializers.ValidationError(
                f"Frequency must be one of: {', '.join(valid_frequencies)}"
            )
        return value

class UserSupplementLogSerializer(serializers.ModelSerializer):
    user_supplement_details = UserSupplementSerializer(source='user_supplement', read_only=True)
    user_supplement_id = serializers.PrimaryKeyRelatedField(
        queryset=UserSupplement.objects.all(), source='user_supplement', write_only=True
    )
    
    class Meta:
        model = UserSupplementLog
        fields = ['id', 'user_supplement_id', 'user_supplement_details', 'date', 'time', 'dosage']
    
    def validate_dosage(self, value):
        """Validate dosage is positive and within reasonable range."""
        if value <= 0:
            raise serializers.ValidationError("Dosage must be greater than 0.")
        if value > 10000:  # Reasonable upper limit
            raise serializers.ValidationError("Dosage is too high. Please check your input.")
        return value
    
    def validate_date(self, value):
        """Validate date is not in the future."""
        if value > timezone.now().date():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        # If date is today, ensure time is not in the future
        log_date = data.get('date')
        log_time = data.get('time')
        
        if log_date and log_time:
            today = timezone.now().date()
            now = timezone.now().time()
            
            if log_date == today and log_time > now:
                raise serializers.ValidationError({
                    'time': 'Time cannot be in the future for today\'s date.'
                })
        
        return data
    









