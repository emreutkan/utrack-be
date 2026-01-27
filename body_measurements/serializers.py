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
    
    def validate_height(self, value):
        """Validate height is within reasonable range (50-300 cm)."""
        if value <= 0:
            raise serializers.ValidationError("Height must be greater than 0.")
        if value < 50 or value > 300:
            raise serializers.ValidationError("Height must be between 50 and 300 cm.")
        return value
    
    def validate_weight(self, value):
        """Validate weight is within reasonable range (20-500 kg)."""
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        if value < 20 or value > 500:
            raise serializers.ValidationError("Weight must be between 20 and 500 kg.")
        return value
    
    def validate_waist(self, value):
        """Validate waist measurement is within reasonable range (30-200 cm)."""
        if value <= 0:
            raise serializers.ValidationError("Waist measurement must be greater than 0.")
        if value < 30 or value > 200:
            raise serializers.ValidationError("Waist measurement must be between 30 and 200 cm.")
        return value
    
    def validate_neck(self, value):
        """Validate neck measurement is within reasonable range (20-80 cm)."""
        if value <= 0:
            raise serializers.ValidationError("Neck measurement must be greater than 0.")
        if value < 20 or value > 80:
            raise serializers.ValidationError("Neck measurement must be between 20 and 80 cm.")
        return value
    
    def validate_hips(self, value):
        """Validate hips measurement is within reasonable range (50-200 cm)."""
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Hips measurement must be greater than 0.")
            if value < 50 or value > 200:
                raise serializers.ValidationError("Hips measurement must be between 50 and 200 cm.")
        return value
    
    def validate(self, data):
        """Validate measurements based on gender and cross-field validation"""
        # Gender will be set from user if not provided in views
        gender = data.get('gender', 'male')  # Default to male if not provided
        hips = data.get('hips')
        waist = data.get('waist')
        neck = data.get('neck')
        
        if gender == 'female' and not hips:
            raise serializers.ValidationError({
                'hips': 'Hips measurement is required for women'
            })
        
        # Cross-field validation: waist should be greater than neck
        if waist and neck and waist <= neck:
            raise serializers.ValidationError({
                'waist': 'Waist measurement must be greater than neck measurement.'
            })
        
        # For women, waist + hips should be greater than neck
        if gender == 'female' and waist and hips and neck:
            if (waist + hips) <= neck:
                raise serializers.ValidationError({
                    'waist': 'The sum of waist and hips measurements must be greater than neck measurement.'
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
    
    def validate_height(self, value):
        """Validate height is within reasonable range (50-300 cm)."""
        if value <= 0:
            raise serializers.ValidationError("Height must be greater than 0.")
        if value < 50 or value > 300:
            raise serializers.ValidationError("Height must be between 50 and 300 cm.")
        return value
    
    def validate_weight(self, value):
        """Validate weight is within reasonable range (20-500 kg)."""
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        if value < 20 or value > 500:
            raise serializers.ValidationError("Weight must be between 20 and 500 kg.")
        return value
    
    def validate_waist(self, value):
        """Validate waist measurement is within reasonable range (30-200 cm)."""
        if value <= 0:
            raise serializers.ValidationError("Waist measurement must be greater than 0.")
        if value < 30 or value > 200:
            raise serializers.ValidationError("Waist measurement must be between 30 and 200 cm.")
        return value
    
    def validate_neck(self, value):
        """Validate neck measurement is within reasonable range (20-80 cm)."""
        if value <= 0:
            raise serializers.ValidationError("Neck measurement must be greater than 0.")
        if value < 20 or value > 80:
            raise serializers.ValidationError("Neck measurement must be between 20 and 80 cm.")
        return value
    
    def validate_hips(self, value):
        """Validate hips measurement is within reasonable range (50-200 cm)."""
        if value is not None:
            if value <= 0:
                raise serializers.ValidationError("Hips measurement must be greater than 0.")
            if value < 50 or value > 200:
                raise serializers.ValidationError("Hips measurement must be between 50 and 200 cm.")
        return value
    
    def validate(self, data):
        gender = data.get('gender')
        hips = data.get('hips')
        waist = data.get('waist')
        neck = data.get('neck')
        
        # If gender is 'female' and hips not provided, raise error
        if gender == 'female' and not hips:
            raise serializers.ValidationError({
                'hips': 'Hips measurement is required for women'
            })
        
        # Cross-field validation: waist should be greater than neck
        if waist and neck and waist <= neck:
            raise serializers.ValidationError({
                'waist': 'Waist measurement must be greater than neck measurement.'
            })
        
        # For women, waist + hips should be greater than neck
        if gender == 'female' and waist and hips and neck:
            if (waist + hips) <= neck:
                raise serializers.ValidationError({
                    'waist': 'The sum of waist and hips measurements must be greater than neck measurement.'
                })
        
        return data


