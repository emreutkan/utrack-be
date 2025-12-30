from django.db import models
from django.utils import timezone
import json

from core.models import TimestampedModel
# Create your models here.

from user.models import CustomUser
from exercise.models import Exercise
class Workout(TimestampedModel):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    datetime = models.DateTimeField(default=timezone.now)  # When the workout actually happened (defaults to created_at if not specified)
    duration = models.PositiveIntegerField(default=0) ## duration is the time in seconds that the workout took
    intensity = models.CharField(max_length=255, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]) ## intensity is the intensity of the workout
    notes = models.TextField(blank=True, null=True) ## notes is a text field that the user can add to the workout
    is_done = models.BooleanField(default=False) ## is_done is a boolean field that indicates whether the workout has been completed
    is_rest_day = models.BooleanField(default=False) ## is_rest_day marks the workout as a rest day but it still counts as a workout
    calories_burned = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True) ## calories burned during the workout
    rest_timer_paused_at = models.DateTimeField(null=True, blank=True) ## timestamp when rest timer was paused/halted
##    body_parts_worked = models.JSONField(default=list, blank=True, null=True) ## body_parts_worked is a json field that contains the body parts worked in the workout
    
    def calculate_calories(self):
        """
        Calculate calories burned using volume-based formula for strength training.
        
        Step 1: Calculate Total Work Volume (weight × reps for all sets)
        Step 2: Apply Energy Cost (2.75 calories per 1000kg lifted)
        Step 3: Apply Difficulty Multiplier (based on exercise type)
        Step 4: Add Metabolic Burn (MET × body_weight × duration_hours)
        
        Formula:
        - Work Burn = (total_volume_kg × energy_cost_per_1000kg × difficulty_multiplier) / 1000
        - Metabolic Burn = MET × body_weight_kg × workout_duration_hours
        - Total = Work Burn + Metabolic Burn
        
        Returns the calculated calories.
        """
        from user.models import UserProfile
        
        # Get user body weight (default to 70kg if not set)
        try:
            profile = UserProfile.objects.get(user=self.user)
            body_weight_kg = float(profile.body_weight) if profile.body_weight else 70.0
        except UserProfile.DoesNotExist:
            body_weight_kg = 70.0  # Default average body weight
        
        # Get all workout exercises with their sets
        workout_exercises = WorkoutExercise.objects.filter(workout=self).select_related('exercise').prefetch_related('sets')
        
        if not workout_exercises.exists():
            # No exercises, return 0
            self.calories_burned = 0
            self.save(update_fields=['calories_burned'])
            return 0.0
        
        # Step 1: Calculate Total Work Volume
        total_volume_kg = 0.0  # Total weight × reps in kg
        total_sets = 0
        compound_count = 0
        isolation_count = 0
        max_weight = 0.0
        total_rest_seconds = 0
        
        # Track exercise types for difficulty multiplier
        high_difficulty_exercises = ['deadlift', 'squat', 'thruster']  # Exercises with 1.2x multiplier
        
        for workout_exercise in workout_exercises:
            exercise = workout_exercise.exercise
            sets = workout_exercise.sets.all()
            
            # Check if exercise is high difficulty
            exercise_name_lower = exercise.name.lower()
            is_high_difficulty = any(term in exercise_name_lower for term in high_difficulty_exercises)
            
            if exercise.category == 'compound':
                compound_count += 1
            else:
                isolation_count += 1
            
            for exercise_set in sets:
                if exercise_set.is_warmup:
                    continue
                
                total_sets += 1
                weight_kg = float(exercise_set.weight) if exercise_set.weight else 0.0
                reps = exercise_set.reps if exercise_set.reps else 0
                
                if weight_kg > 0 and reps > 0:
                    # Calculate volume for this set
                    set_volume = weight_kg * reps
                    total_volume_kg += set_volume
                    max_weight = max(max_weight, weight_kg)
                
                if exercise_set.rest_time_before_set:
                    total_rest_seconds += exercise_set.rest_time_before_set
        
        # Step 2: Apply Energy Cost (2.75 calories per 1000kg - average of 2.5-3.0 range)
        energy_cost_per_1000kg = 2.75
        work_burn = (total_volume_kg * energy_cost_per_1000kg) / 1000.0
        
        # Step 3: Apply Difficulty Multiplier based on exercise types
        compound_ratio = compound_count / (compound_count + isolation_count) if (compound_count + isolation_count) > 0 else 0.5
        
        # Determine difficulty multiplier
        # High (1.2x): Mostly compound exercises, especially deadlifts/squats
        # Medium (1.0x): Standard compound exercises
        # Low (0.8x): Mostly isolation exercises
        if compound_ratio >= 0.7:
            difficulty_multiplier = 1.2  # High - mostly compound
        elif compound_ratio >= 0.4:
            difficulty_multiplier = 1.0  # Medium - mixed
        else:
            difficulty_multiplier = 0.8  # Low - mostly isolation
        
        # Apply difficulty multiplier to work burn
        work_burn = work_burn * difficulty_multiplier
        
        # Step 4: Calculate Metabolic Burn using MET values
        # Determine MET value based on workout intensity
        if self.intensity == 'high':
            met_value = 6.0  # Vigorous
        elif self.intensity == 'low':
            met_value = 3.5  # Light
        else:
            # Auto-determine based on workout characteristics
            if max_weight > 100 and total_rest_seconds / total_sets > 180:  # Heavy weights, long rest
                met_value = 5.0  # Moderate (powerlifting style)
            elif compound_ratio > 0.5 and max_weight > 50:
                met_value = 5.0  # Moderate (standard bodybuilding)
            else:
                met_value = 3.5  # Light
        
        # Calculate workout duration in hours
        workout_duration_hours = self.duration / 3600.0 if self.duration > 0 else 0
        
        # If duration is not set, estimate from sets and rest
        if workout_duration_hours < 0.1:  # Less than 6 minutes
            # Estimate: ~30 seconds per set + rest time
            estimated_set_time = total_sets * 0.5  # 30 seconds per set
            estimated_total_seconds = estimated_set_time * 60 + total_rest_seconds
            # Cap estimated duration at 3 hours (10800 seconds) to prevent unrealistic values
            estimated_total_seconds = min(estimated_total_seconds, 10800)
            workout_duration_hours = estimated_total_seconds / 3600.0
        
        # Metabolic burn = MET × body_weight × duration_hours
        metabolic_burn = met_value * body_weight_kg * workout_duration_hours
        
        # Total calories = Work Burn + Metabolic Burn
        calories = work_burn + metabolic_burn
        
        # Cap calories at reasonable maximum (e.g., 1500 calories for extreme workouts)
        max_calories = 1500.0
        calories = min(calories, max_calories)
        
        # Ensure minimum calories for any workout (at least 30 calories)
        calories = max(calories, 30.0)
        
        calories = round(calories, 2)
        self.calories_burned = calories
        self.save(update_fields=['calories_burned'])
        return calories
    
    def calculate_muscle_recovery(self):
        """
        Calculate fatigue scores and recovery times for all muscles worked in this workout.
        Creates MuscleRecovery records for each muscle group.
        
        Fatigue Score Formula:
        - Base: 1.0 per set
        - RIR Multiplier: 0 RIR = 1.5x, 1-2 RIR = 1.0x, 3-4 RIR = 0.7x, 5+ RIR = 0.4x
        - Exercise Type: Compound = 1.2x, Isolation = 0.8x
        - Rest Time: <60s = +0.2x (metabolic stress), >3min = +0.1x (CNS fatigue)
        
        Recovery Hours Formula:
        - Baseline: 24 hours
        - Muscle Size: Large (quads, back, chest) = +12h, Small (biceps, calves, rear delts) = -6h
        - Volume Penalty: >8 sets = +12h, >15 sets = +24h
        - Metabolic Fatigue: Short rest on compound = +4h
        """
        
        # Muscle size categories
        LARGE_MUSCLES = ['quads', 'lats', 'chest', 'hamstrings', 'glutes']
        SMALL_MUSCLES = ['biceps', 'calves', 'traps', 'forearms', 'abs', 'obliques']
        
        # Get all workout exercises with sets
        workout_exercises = WorkoutExercise.objects.filter(workout=self).select_related('exercise').prefetch_related('sets')
        
        # Dictionary to accumulate fatigue per muscle
        muscle_fatigue = {}  # {muscle_group: {'fatigue_score': float, 'sets': int, 'has_short_rest_compound': bool}}
        
        for workout_exercise in workout_exercises:
            exercise = workout_exercise.exercise
            sets = workout_exercise.sets.all()
            
            # Skip if no sets
            if not sets.exists():
                continue
            
            # Determine exercise type multiplier
            exercise_multiplier = 1.2 if exercise.category == 'compound' else 0.8
            
            # Track if this exercise has short rest (for metabolic fatigue bonus)
            has_short_rest = False
            
            for exercise_set in sets:
                # Skip warmup sets
                if exercise_set.is_warmup:
                    continue
                
                # Calculate RIR multiplier
                rir = exercise_set.reps_in_reserve if exercise_set.reps_in_reserve else 0
                if rir == 0:
                    rir_multiplier = 1.5  # Failure
                elif rir <= 2:
                    rir_multiplier = 1.0  # Baseline
                elif rir <= 4:
                    rir_multiplier = 0.7
                else:
                    rir_multiplier = 0.4  # Warm-up territory
                
                # Rest time modifier
                rest_time = exercise_set.rest_time_before_set if exercise_set.rest_time_before_set else 0
                rest_modifier = 0.0
                if rest_time < 60:  # Short rest (<60s)
                    rest_modifier = 0.2  # Metabolic stress
                    if exercise.category == 'compound':
                        has_short_rest = True
                elif rest_time > 180:  # Long rest (>3min)
                    rest_modifier = 0.1  # CNS fatigue
                
                # Calculate fatigue score for this set
                set_fatigue = 1.0 * rir_multiplier * exercise_multiplier * (1.0 + rest_modifier)
                
                # Distribute to primary muscle (100%)
                primary_muscle = exercise.primary_muscle
                if primary_muscle not in muscle_fatigue:
                    muscle_fatigue[primary_muscle] = {'fatigue_score': 0.0, 'sets': 0, 'has_short_rest_compound': False}
                
                muscle_fatigue[primary_muscle]['fatigue_score'] += set_fatigue
                muscle_fatigue[primary_muscle]['sets'] += 1
                if has_short_rest:
                    muscle_fatigue[primary_muscle]['has_short_rest_compound'] = True
                
                # Distribute to secondary muscles (40%)
                secondary_muscles = exercise.secondary_muscles or []
                for secondary_muscle in secondary_muscles:
                    if secondary_muscle not in muscle_fatigue:
                        muscle_fatigue[secondary_muscle] = {'fatigue_score': 0.0, 'sets': 0, 'has_short_rest_compound': False}
                    
                    muscle_fatigue[secondary_muscle]['fatigue_score'] += set_fatigue * 0.4
                    muscle_fatigue[secondary_muscle]['sets'] += 1
        
        # Calculate recovery hours for each muscle and create MuscleRecovery records
        workout_datetime = self.datetime or self.created_at
        recovery_records = []
        
        for muscle_group, data in muscle_fatigue.items():
            fatigue_score = data['fatigue_score']
            total_sets = data['sets']
            has_short_rest_compound = data['has_short_rest_compound']
            
            # Base recovery hours
            recovery_hours = 24
            
            # Muscle size adjustment
            if muscle_group in LARGE_MUSCLES:
                recovery_hours += 12
            elif muscle_group in SMALL_MUSCLES:
                recovery_hours -= 6
            
            # Volume penalty
            if total_sets > 15:
                recovery_hours += 24
            elif total_sets > 8:
                recovery_hours += 12
            
            # Metabolic fatigue bonus (short rest on compound)
            if has_short_rest_compound:
                recovery_hours += 4
            
            # Calculate recovery_until timestamp
            recovery_until = workout_datetime + timezone.timedelta(hours=recovery_hours)
            
            # Create or update MuscleRecovery record
            recovery_record, created = MuscleRecovery.objects.update_or_create(
                user=self.user,
                muscle_group=muscle_group,
                source_workout=self,
                defaults={
                    'fatigue_score': round(fatigue_score, 2),
                    'total_sets': total_sets,
                    'recovery_hours': recovery_hours,
                    'recovery_until': recovery_until,
                    'is_recovered': timezone.now() >= recovery_until
                }
            )
            recovery_records.append(recovery_record)
        
        return recovery_records


class WorkoutExercise(TimestampedModel):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)  # Link to Exercise template
    order = models.PositiveIntegerField(default=0)
    one_rep_max = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # Calculated 1RM from sets
    class Meta:
        ordering = ['order']

# workout/models.py - ExerciseSet
class ExerciseSet(TimestampedModel):
    workout_exercise = models.ForeignKey(WorkoutExercise, on_delete=models.CASCADE, related_name='sets')
    set_number = models.PositiveIntegerField()  # Keep this, remove 'set'
    reps = models.PositiveIntegerField(default=0)  # Change 'rep' to 'reps'
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # Change to DecimalField
    rest_time_before_set = models.PositiveIntegerField(default=0)
    is_warmup = models.BooleanField(default=False)
    reps_in_reserve = models.PositiveIntegerField(default=0)
    eccentric_time = models.PositiveIntegerField(null=True, blank=True)  # Time under tension - eccentric phase (seconds)
    concentric_time = models.PositiveIntegerField(null=True, blank=True)  # Time under tension - concentric phase (seconds)
    total_tut = models.PositiveIntegerField(null=True, blank=True)  # Total time under tension (seconds) - optional

    class Meta:
        ordering = ['set_number']
    
    def __str__(self):
        return f"Set {self.set_number} - {self.reps} reps @ {self.weight}"

class TemplateWorkout(TimestampedModel):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    exercises = models.ManyToManyField(Exercise, through='TemplateWorkoutExercise')
    notes = models.TextField(blank=True, null=True)  # Optional notes for the template

    def __str__(self):
        return self.title

class TemplateWorkoutExercise(TimestampedModel):
    template_workout = models.ForeignKey(TemplateWorkout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

class TrainingResearch(TimestampedModel):
    """Research-backed training information and recommendations"""
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField()
    
    CATEGORY_CHOICES = [
        ('INTENSITY_GUIDELINES', 'Intensity Guidelines'),
        ('PROTEIN_SYNTHESIS', 'Protein Synthesis'),
        ('MUSCLE_GROUPS', 'Muscle Groups'),
        ('MUSCLE_RECOVERY', 'Muscle Recovery'),
        ('REST_PERIODS', 'Rest Periods'),
        ('TRAINING_FREQUENCY', 'Training Frequency'),
        ('BODY_MEASUREMENTS', 'Body Measurements'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = models.JSONField(default=list, blank=True)
    
    # Source information
    source_title = models.CharField(max_length=255, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    source_authors = models.JSONField(default=list, blank=True)
    publication_date = models.DateField(blank=True, null=True)
    
    # Evidence quality
    evidence_level = models.CharField(max_length=50, blank=True, null=True)  # high, moderate, low
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)  # 0.0 to 1.0
    
    # Applicability
    applicable_muscle_groups = models.JSONField(default=list, blank=True)  # ["chest", "back", "all"]
    applicable_exercise_types = models.JSONField(default=list, blank=True)  # ["compound", "isolation", "all"]
    
    # Parameters (JSON field for flexible data storage)
    parameters = models.JSONField(default=dict, blank=True)  # e.g., {"recovery_time_hours": 48, "optimal_rpe_range": [7, 9]}
    
    is_active = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)  # Higher priority = shown first
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title

class MuscleRecovery(TimestampedModel):
    """
    Tracks fatigue and recovery status for each muscle group per user.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    muscle_group = models.CharField(max_length=50, choices=Exercise.MUSCLE_GROUPS)
    
    # Fatigue tracking
    fatigue_score = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    total_sets = models.PositiveIntegerField(default=0)  # Total sets for this muscle in the workout
    
    # Recovery timing
    recovery_hours = models.PositiveIntegerField(default=24)  # Hours until fully recovered
    recovery_until = models.DateTimeField(null=True, blank=True)  # Timestamp when recovery is complete
    
    # Source workout
    source_workout = models.ForeignKey(Workout, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_recovered = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-recovery_until']
        unique_together = [['user', 'muscle_group', 'source_workout']]  # One recovery record per muscle per workout
    
    def __str__(self):
        return f"{self.user.email} - {self.muscle_group} - {self.recovery_hours}h"
    
    def update_recovery_status(self):
        """Update is_recovered based on recovery_until timestamp"""
        if self.recovery_until:
            self.is_recovered = timezone.now() >= self.recovery_until
            self.save(update_fields=['is_recovered'])
        return self.is_recovered
