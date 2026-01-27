from rest_framework import serializers
from .models import Supplement, UserSupplement, UserSupplementLog

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

class UserSupplementLogSerializer(serializers.ModelSerializer):
    user_supplement_details = UserSupplementSerializer(source='user_supplement', read_only=True)
    user_supplement_id = serializers.PrimaryKeyRelatedField(
        queryset=UserSupplement.objects.all(), source='user_supplement', write_only=True
    )
    
    class Meta:
        model = UserSupplementLog
        fields = ['id', 'user_supplement_id', 'user_supplement_details', 'date', 'time', 'dosage']
    









