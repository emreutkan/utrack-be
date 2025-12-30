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
        Calculate calories burned using simplified volume-based formula for strength training.
        
        Formula: Calories = Total Volume (kg) × Multiplier
        
        The multiplier already includes:
        - Mechanical work (lifting the weight)
        - Metabolic cost (isometric contraction, eccentric phase, EPOC)
        - Rest periods (elevated heart rate between sets)
        
        Multipliers:
        - Compound exercises: 0.007 (e.g., rows, squats, deadlifts)
        - Isolation exercises: 0.004 (e.g., curls, tricep extensions)
        - Mixed workouts: Weighted average based on compound ratio
        
        Example: 2 sets × 8 reps × 150kg = 2,400kg volume
        Compound: 2,400 × 0.007 = 16.8 calories
        
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
        
        # Calculate calories using simplified volume-based formula
        # The 0.007 constant for compound exercises already factors in:
        # - Work calories (2.5-3 kcal per 1000kg)
        # - Metabolic cost multiplier (2.5-3x for isometric, eccentric, rest periods)
        # - Average rest for compound lifts
        compound_ratio = compound_count / (compound_count + isolation_count) if (compound_count + isolation_count) > 0 else 0.5
        
        # Determine multiplier based on exercise type
        # Compound exercises: 0.007 (includes work + metabolic cost + rest)
        # Isolation exercises: 0.004 (lower metabolic cost, less EPOC)
        if compound_ratio >= 0.7:
            # Mostly compound exercises
            calories_per_kg = 0.007
        elif compound_ratio >= 0.4:
            # Mixed - use weighted average
            calories_per_kg = (compound_ratio * 0.007) + ((1 - compound_ratio) * 0.004)
        else:
            # Mostly isolation exercises
            calories_per_kg = 0.004
        
        # Simple formula: Total Volume × Calories per kg
        calories = total_volume_kg * calories_per_kg
        
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
        Based on sports science research: recovery is non-linear, exercise-specific, and multi-system.
        
        Fatigue Score Formula:
        - Base: 1.0 per set
        - RIR Multiplier: 0 RIR = 1.5x, 1-2 RIR = 1.0x, 3-4 RIR = 0.7x, 5+ RIR = 0.4x
        - Exercise Type: Compound = 1.2x, Isolation = 0.8x
        - Rest Time: <60s = +0.2x (metabolic stress), >3min = +0.1x (CNS fatigue)
        
        Recovery Hours Formula (Exercise-Specific):
        - Small muscles (biceps, calves): 36h base (faster protein synthesis)
        - Large muscles (quads, back, chest): 48h base (more structural damage)
        - Medium muscles (shoulders): 42h base
        - Fatigue multiplier: High fatigue (>20) = 1.5x, Moderate (>12) = 1.3x, Low (>6) = 1.1x
        - Volume penalty: >8 sets = +12h, >15 sets = +24h
        - Metabolic fatigue: Short rest on compound = +6h
        - Novelty penalty: Exercise not done in 4+ weeks = +12h (unaccustomed exercise causes more damage)
        - Eccentric emphasis: If eccentric_time is set = +8h (extends structural repair phase, more micro-tears)
        
        Recovery follows J-curve (non-linear):
        - 0-24h: Inflammation phase (slower recovery, 0-30%)
        - 24-48h: Protein synthesis peak (accelerated recovery, 30-70%)
        - 48h+: Structural repair completion (70-100%)
        """
        
        # Muscle size categories
        LARGE_MUSCLES = ['quads', 'lats', 'chest', 'hamstrings', 'glutes']
        SMALL_MUSCLES = ['biceps', 'calves', 'traps', 'forearms', 'abs', 'obliques']
        
        # Get all workout exercises with sets
        workout_exercises = WorkoutExercise.objects.filter(workout=self).select_related('exercise').prefetch_related('sets')
        
        # Dictionary to accumulate fatigue per muscle
        # Track: fatigue_score, sets, has_short_rest_compound, has_eccentric_emphasis, is_novel_exercise
        muscle_fatigue = {}  # {muscle_group: {'fatigue_score': float, 'sets': int, 'has_short_rest_compound': bool, 'has_eccentric_emphasis': bool, 'is_novel_exercise': bool}}
        
        # Check for novel exercises (not done in 4+ weeks) per muscle group
        workout_datetime = self.datetime or self.created_at
        four_weeks_ago = workout_datetime - timezone.timedelta(weeks=4)
        
        for workout_exercise in workout_exercises:
            exercise = workout_exercise.exercise
            sets = workout_exercise.sets.all()
            
            # Skip if no sets
            if not sets.exists():
                continue
            
            # Check if this exercise is novel (not done in 4+ weeks)
            # Check if this specific exercise was done recently
            recent_workout_exercises = WorkoutExercise.objects.filter(
                exercise=exercise,
                workout__user=self.user,
                workout__datetime__gte=four_weeks_ago,
                workout__datetime__lt=workout_datetime
            ).exists()
            is_novel = not recent_workout_exercises
            
            # Determine exercise type multiplier
            exercise_multiplier = 1.2 if exercise.category == 'compound' else 0.8
            
            # Track if this exercise has short rest (for metabolic fatigue bonus)
            has_short_rest = False
            # Track if any sets have eccentric emphasis (eccentric_time is not null)
            has_eccentric_emphasis = False
            
            for exercise_set in sets:
                # Skip warmup sets
                if exercise_set.is_warmup:
                    continue
                
                # Check for eccentric emphasis (eccentric_time is not null)
                if exercise_set.eccentric_time is not None and exercise_set.eccentric_time > 0:
                    has_eccentric_emphasis = True
                
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
                    muscle_fatigue[primary_muscle] = {
                        'fatigue_score': 0.0, 
                        'sets': 0, 
                        'has_short_rest_compound': False,
                        'has_eccentric_emphasis': False,
                        'is_novel_exercise': False
                    }
                
                muscle_fatigue[primary_muscle]['fatigue_score'] += set_fatigue
                muscle_fatigue[primary_muscle]['sets'] += 1
                if has_short_rest:
                    muscle_fatigue[primary_muscle]['has_short_rest_compound'] = True
                if has_eccentric_emphasis:
                    muscle_fatigue[primary_muscle]['has_eccentric_emphasis'] = True
                if is_novel:
                    muscle_fatigue[primary_muscle]['is_novel_exercise'] = True
                
                # Distribute to secondary muscles (40%)
                secondary_muscles = exercise.secondary_muscles or []
                for secondary_muscle in secondary_muscles:
                    if secondary_muscle not in muscle_fatigue:
                        muscle_fatigue[secondary_muscle] = {
                            'fatigue_score': 0.0, 
                            'sets': 0, 
                            'has_short_rest_compound': False,
                            'has_eccentric_emphasis': False,
                            'is_novel_exercise': False
                        }
                    
                    muscle_fatigue[secondary_muscle]['fatigue_score'] += set_fatigue * 0.4
                    muscle_fatigue[secondary_muscle]['sets'] += 1
                    if has_eccentric_emphasis:
                        muscle_fatigue[secondary_muscle]['has_eccentric_emphasis'] = True
                    if is_novel:
                        muscle_fatigue[secondary_muscle]['is_novel_exercise'] = True
        
        # Calculate recovery hours for each muscle and create MuscleRecovery records
        # Based on sports science: recovery is non-linear, exercise-specific, and involves multiple systems
        workout_datetime = self.datetime or self.created_at
        recovery_records = []
        
        for muscle_group, data in muscle_fatigue.items():
            fatigue_score = data['fatigue_score']
            total_sets = data['sets']
            has_short_rest_compound = data['has_short_rest_compound']
            has_eccentric_emphasis = data.get('has_eccentric_emphasis', False)
            is_novel_exercise = data.get('is_novel_exercise', False)
            
            # Base recovery hours - varies by muscle size and exercise type
            # Small muscles (biceps, calves) recover faster: 24-36h for protein synthesis
            # Large muscles (quads, back) need more time: 48-72h for full recovery
            if muscle_group in LARGE_MUSCLES:
                base_recovery = 48  # Large muscles need more time for structural repair
            elif muscle_group in SMALL_MUSCLES:
                base_recovery = 36  # Small muscles recover faster
            else:
                base_recovery = 42  # Medium muscles (shoulders, etc.)
            
            # Fatigue-based adjustment (more fatigue = longer recovery)
            # High fatigue (failure sets, high volume) extends recovery significantly
            fatigue_multiplier = 1.0
            if fatigue_score > 20:  # Very high fatigue
                fatigue_multiplier = 1.5
            elif fatigue_score > 12:  # High fatigue
                fatigue_multiplier = 1.3
            elif fatigue_score > 6:  # Moderate fatigue
                fatigue_multiplier = 1.1
            
            recovery_hours = base_recovery * fatigue_multiplier
            
            # Volume penalty (more sets = more damage = longer recovery)
            # Research shows >15 sets can extend recovery to 72-96h for large muscles
            if total_sets > 15:
                recovery_hours += 24  # Significant volume extension
            elif total_sets > 8:
                recovery_hours += 12  # Moderate volume extension
            
            # Metabolic fatigue (short rest on compound = more systemic stress)
            if has_short_rest_compound:
                recovery_hours += 6  # Metabolic stress extends recovery
            
            # Novelty penalty: Unaccustomed exercise (not done in 4+ weeks) causes more damage
            # Research shows novel exercises cause significantly more structural damage
            if is_novel_exercise:
                recovery_hours += 12  # +12h penalty for novel exercises
            
            # Eccentric emphasis: Heavy negatives extend structural repair phase (48h+)
            # Eccentrics cause the most mechanical tension and micro-tears
            # Only applies if eccentric_time is not null in database
            if has_eccentric_emphasis:
                recovery_hours += 8  # Extends structural repair phase
            
            # Cap recovery at reasonable maximum (96 hours for extreme cases)
            recovery_hours = min(recovery_hours, 96)
            
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

class WorkoutMuscleRecovery(TimestampedModel):
    """
    Tracks muscle recovery progress before and after workouts.
    Creates entries when workout starts (pre) and when workout completes (post).
    """
    CONDITION_CHOICES = [
        ('pre', 'Pre-Workout'),
        ('post', 'Post-Workout'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='muscle_recovery_records')
    muscle_group = models.CharField(max_length=50, choices=Exercise.MUSCLE_GROUPS)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)  # 'pre' or 'post'
    recovery_progress = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage 0-100
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [['user', 'workout', 'muscle_group', 'condition']]  # One record per muscle per condition per workout
    
    def __str__(self):
        return f"{self.user.email} - {self.workout.id} - {self.muscle_group} - {self.condition} - {self.recovery_progress}%"
