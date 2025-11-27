from rest_framework import serializers
from .models import Workout, WorkoutExercise
from django.utils import timezone

class CreateWorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'title'] # id is included but we dont send it from the frontend to the backend
        read_only_fields = ['id'] # then why did we write it in the class Meta? because we want to include it in the response

    def create(self, validated_data):
        user = self.context['request'].user
        current_date = timezone.now().date()
        
        # Handle title logic
        if not validated_data.get('title'):
            validated_data['title'] = current_date.strftime("%B, %d")
            
        # Create with user
        workout = Workout.objects.create(
            user=user,
            **validated_data
        )
        return workout

class CompleteWorkoutSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True) # Add created_at explicitly

    class Meta:
        model = Workout
        # Expose created_at so frontend knows the date
        fields = ['id', 'title', 'notes', 'created_at', 'duration', 'intensity', 'is_done']
        
        # Restrict what can be EDITED
        read_only_fields = ['id', 'user', 'created_at', 'duration', 'intensity', 'is_done']
        
    def update(self, instance, validated_data):
        # 1. Mark as done
        validated_data['is_done'] = True
        
        # 2. Calculate Duration (If you want to do this, we need a logic. 
        # Calculate Duration using created_at
        # timezone.now() is the "Finish Time"
        # instance.created_at is the "Start Time"
        time_diff = timezone.now() - instance.created_at
        
        # total_seconds() gives precise diff. /60 for minutes.
        # Using int() creates a floor value (25.9 mins -> 25 mins)
        # Using round() is better (25.9 -> 26 mins)
        validated_data['duration'] = int(time_diff.total_seconds() / 60) 
        
        # 3. Calculate Intensity (Placeholder logic)
        # instance.intensity = calculate_intensity(instance)
        
        return super().update(instance, validated_data)

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutExercise
        fields = ['id', 'workout', 'exercise', 'order']
        read_only_fields = ['id']
