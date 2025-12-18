from rest_framework import serializers
from .models import Workout, WorkoutExercise, ExerciseSet, TemplateWorkout, TemplateWorkoutExercise
from django.utils import timezone
from datetime import datetime
from exercise.serializers import ExerciseSerializer
from exercise.models import Exercise

class CreateWorkoutSerializer(serializers.ModelSerializer):
    workout_date = serializers.DateTimeField(required=False, write_only=True)  # Accept datetime
    date = serializers.DateTimeField(required=False, write_only=True)  # Also accept 'date' for compatibility
    title = serializers.CharField(required=False)  # Make title optional
    
    class Meta:
        model = Workout
        fields = ['id', 'title', 'workout_date', 'date', 'is_done', 'is_rest_day']
        read_only_fields = ['id']
    
    def validate(self, data):
        # If it's a rest day, ignore title and is_done from request
        if data.get('is_rest_day', False):
            # Remove title and is_done if provided (we'll set them automatically)
            data.pop('title', None)
            data.pop('is_done', None)
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        is_rest_day = validated_data.get('is_rest_day', False)
        
        # Accept either 'workout_date' or 'date'
        workout_datetime = validated_data.pop('workout_date', None) or validated_data.pop('date', None)
        
        # Get workout datetime (provided or default to now, which will match created_at)
        if workout_datetime:
            # If it's a naive datetime, make it timezone-aware
            if timezone.is_naive(workout_datetime):
                workout_datetime = timezone.make_aware(workout_datetime)
            # Set the datetime field
            validated_data['datetime'] = workout_datetime
            workout_date = workout_datetime.date()
        else:
            # If not provided, use current time (will be same as created_at)
            current_time = timezone.now()
            validated_data['datetime'] = current_time
            workout_date = current_time.date()
        
        # Handle title logic
        if is_rest_day:
            # Rest days always have title "Rest Day"
            validated_data['title'] = "Rest Day"
            validated_data['is_done'] = True
        elif not validated_data.get('title'):
            # Regular workouts default to date format
            validated_data['title'] = workout_date.strftime("%B, %d")
        
        # Create workout
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

class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['id', 'workout_exercise', 'set_number', 'reps', 'weight', 'rest_time_before_set', 'is_warmup', 'reps_in_reserve']
        read_only_fields = ['id']

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    # Accept exercise as ID when writing, return full object when reading
    exercise = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    # Add this line to fetch related sets
    sets = ExerciseSetSerializer(many=True, read_only=True) 
    
    class Meta:
        model = WorkoutExercise
        fields = ['id', 'workout', 'exercise', 'order', 'sets']
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        # Override to return full exercise object instead of just ID
        representation = super().to_representation(instance)
        # Replace exercise ID with full exercise object
        if instance.exercise:
            representation['exercise'] = ExerciseSerializer(instance.exercise).data
        return representation

class UpdateWorkoutSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(required=False, write_only=True)  # Accept datetime for updating
    
    class Meta:
        model = Workout
        fields = ['id', 'title', 'date', 'duration', 'intensity', 'notes', 'is_done']
        read_only_fields = ['id']
    
    def update(self, instance, validated_data):
        # Handle datetime update if provided
        workout_datetime = validated_data.pop('date', None)
        if workout_datetime:
            # If it's a naive datetime, make it timezone-aware
            if timezone.is_naive(workout_datetime):
                workout_datetime = timezone.make_aware(workout_datetime)
            validated_data['datetime'] = workout_datetime
        
        # Update workout fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class GetWorkoutSerializer(serializers.ModelSerializer):
    # Add this field to fetch related exercises
    # Note: 'workoutexercise_set' is the default related name. 
    # If you want it to be called 'exercises', you can rename it in the SerializerField
    exercises = WorkoutExerciseSerializer(source='workoutexercise_set', many=True, read_only=True)
    total_volume = serializers.SerializerMethodField()
    primary_muscles_worked = serializers.SerializerMethodField()
    secondary_muscles_worked = serializers.SerializerMethodField()

    class Meta:
        model = Workout
        fields = ['id', 'title', 'datetime', 'duration', 'intensity', 'notes', 'is_done', 'is_rest_day', 'created_at', 'updated_at', 'exercises', 'total_volume', 'primary_muscles_worked', 'secondary_muscles_worked']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_volume(self, obj):
        """Calculate total volume (sum of weight * reps for all sets)"""
        total = 0
        workout_exercises = WorkoutExercise.objects.filter(workout=obj).prefetch_related('sets')
        for workout_exercise in workout_exercises:
            for exercise_set in workout_exercise.sets.all():
                total += float(exercise_set.weight) * exercise_set.reps
        return round(total, 2)
    
    def get_primary_muscles_worked(self, obj):
        """Get unique primary muscle groups from all exercises"""
        workout_exercises = WorkoutExercise.objects.filter(workout=obj).select_related('exercise')
        primary_muscles = set()
        for workout_exercise in workout_exercises:
            exercise = workout_exercise.exercise
            if exercise and exercise.primary_muscle:
                primary_muscles.add(exercise.primary_muscle)
        return sorted(list(primary_muscles))
    
    def get_secondary_muscles_worked(self, obj):
        """Get unique secondary muscle groups from all exercises"""
        workout_exercises = WorkoutExercise.objects.filter(workout=obj).select_related('exercise')
        secondary_muscles = set()
        for workout_exercise in workout_exercises:
            exercise = workout_exercise.exercise
            if exercise and exercise.secondary_muscles:
                for muscle in exercise.secondary_muscles:
                    if muscle:
                        secondary_muscles.add(muscle)
        return sorted(list(secondary_muscles))

class TemplateWorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    
    class Meta:
        model = TemplateWorkoutExercise
        fields = ['id', 'exercise', 'order']
        read_only_fields = ['id']

class CreateTemplateWorkoutSerializer(serializers.ModelSerializer):
    exercises = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text="List of exercise IDs"
    )
    
    class Meta:
        model = TemplateWorkout
        fields = ['id', 'title', 'exercises', 'notes']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        user = self.context['request'].user
        exercise_ids = validated_data.pop('exercises', [])
        
        # Create template workout
        template_workout = TemplateWorkout.objects.create(
            user=user,
            **validated_data
        )
        
        # Add exercises with order
        for order, exercise_id in enumerate(exercise_ids, start=1):
            from exercise.models import Exercise
            try:
                exercise = Exercise.objects.get(id=exercise_id)
                TemplateWorkoutExercise.objects.create(
                    template_workout=template_workout,
                    exercise=exercise,
                    order=order
                )
            except Exercise.DoesNotExist:
                continue  # Skip invalid exercise IDs
        
        return template_workout

class GetTemplateWorkoutSerializer(serializers.ModelSerializer):
    exercises = TemplateWorkoutExerciseSerializer(source='templateworkoutexercise_set', many=True, read_only=True)
    primary_muscle_groups = serializers.SerializerMethodField()
    secondary_muscle_groups = serializers.SerializerMethodField()
    
    class Meta:
        model = TemplateWorkout
        fields = ['id', 'title', 'exercises', 'primary_muscle_groups', 'secondary_muscle_groups', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_primary_muscle_groups(self, obj):
        """Get unique primary muscle groups from all exercises"""
        template_exercises = TemplateWorkoutExercise.objects.filter(template_workout=obj).select_related('exercise')
        primary_muscles = set()
        for template_exercise in template_exercises:
            exercise = template_exercise.exercise
            if exercise.primary_muscle:
                primary_muscles.add(exercise.primary_muscle)
        return sorted(list(primary_muscles))
    
    def get_secondary_muscle_groups(self, obj):
        """Get unique secondary muscle groups from all exercises"""
        template_exercises = TemplateWorkoutExercise.objects.filter(template_workout=obj).select_related('exercise')
        secondary_muscles = set()
        for template_exercise in template_exercises:
            exercise = template_exercise.exercise
            if exercise.secondary_muscles:
                for muscle in exercise.secondary_muscles:
                    if muscle:
                        secondary_muscles.add(muscle)
        return sorted(list(secondary_muscles))