from rest_framework import serializers
from .models import BodyMeasurement

class BodyMeasurementSerializer(serializers.ModelSerializer):
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=False, help_text="Optional - uses user's gender from database if not provided")
    
    class Meta:
        model = BodyMeasurement
        fields = [
            'id', 'height', 'weight', 'waist', 'neck', 'hips',
            'body_fat_percentage', 'gender', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'body_fat_percentage', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate measurements based on gender"""
        # Gender will be set from user if not provided in views
        gender = data.get('gender', 'male')  # Default to male if not provided
        hips = data.get('hips')
        
        if gender == 'female' and not hips:
            raise serializers.ValidationError({
                'hips': 'Hips measurement is required for women'
            })
        
        # Basic validation - measurements should be positive
        for field in ['height', 'weight', 'waist', 'neck']:
            if data.get(field) and data[field] <= 0:
                raise serializers.ValidationError({
                    field: f'{field} must be greater than 0'
                })
        
        if hips and hips <= 0:
            raise serializers.ValidationError({
                'hips': 'hips must be greater than 0'
            })
        
        return data
    
    def create(self, validated_data):
        """Override create to set gender from user if not provided"""
        user = self.context['request'].user
        if 'gender' not in validated_data or not validated_data.get('gender'):
            validated_data['gender'] = user.gender or 'male'
        return super().create(validated_data)

class CalculateBodyFatSerializer(serializers.Serializer):
    """Serializer for body fat calculation endpoint"""
    height = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Height in cm")
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    waist = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Waist measurement in cm")
    neck = serializers.DecimalField(max_digits=5, decimal_places=2, help_text="Neck measurement in cm")
    hips = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True, help_text="Hips measurement in cm (required for women)")
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')], required=False, help_text="Optional - uses user's gender from database if not provided")
    
    def validate(self, data):
        gender = data.get('gender')
        hips = data.get('hips')
        
        # If gender is 'female' and hips not provided, raise error
        if gender == 'female' and not hips:
            raise serializers.ValidationError({
                'hips': 'Hips measurement is required for women'
            })
        
        return data


