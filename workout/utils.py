"""
Utility functions for workout operations.
"""
from django.utils import timezone
from .models import Workout, WorkoutExercise, ExerciseSet, MuscleRecovery, WorkoutMuscleRecovery
from exercise.models import Exercise


def calculate_rest_status(elapsed_seconds, category):
    """
    Calculate rest status based on elapsed time and exercise category.
    Returns status object with text, color, and goals.
    """
    is_compound = category and category.lower() == 'compound'
    
    # Thresholds in seconds
    phase1_limit = 90 if is_compound else 60  # Red light limit
    phase2_limit = 180 if is_compound else 90  # Yellow light limit
    
    if elapsed_seconds < phase1_limit:
        return {
            "text": "Rest",
            "color": "#FF3B30",
            "goal": phase1_limit,
            "max_goal": phase2_limit
        }
    elif elapsed_seconds < phase2_limit:
        return {
            "text": "Recharging...",
            "color": "#FF9F0A",
            "goal": phase2_limit,
            "max_goal": phase2_limit
        }
    else:
        return {
            "text": "Ready to Go!",
            "color": "#34C759",
            "goal": phase2_limit,
            "max_goal": phase2_limit
        }


def calculate_one_rep_max(weight, reps):
    """
    Calculate 1RM using Brzycki formula.
    Formula: 1RM = weight / (1.0278 - 0.0278 × reps)
    """
    if reps <= 0 or weight <= 0:
        return None
    
    # Brzycki formula
    denominator = 1.0278 - (0.0278 * reps)
    if denominator <= 0:
        return None
    
    one_rm = float(weight) / denominator
    return round(one_rm, 2)


def calculate_workout_calories(workout):
    """
    Calculate total calories burned for a workout using MET method.
    Delegates to the workout model's calculate_calories method.
    
    Returns: Total calories burned (float)
    """
    return workout.calculate_calories()


def get_current_recovery_progress(user):
    """
    Get current recovery progress (percentage) for all muscle groups.
    Returns dict: {muscle_group: recovery_percentage}
    """
    all_muscle_groups = [choice[0] for choice in Exercise.MUSCLE_GROUPS]
    recovery_progress = {}
    
    # Get most recent recovery records
    all_records = MuscleRecovery.objects.filter(
        user=user,
        muscle_group__in=all_muscle_groups
    ).select_related('source_workout').order_by(
        'muscle_group',
        '-source_workout__datetime',
        '-recovery_until'
    )
    
    seen_groups = set()
    recovery_records = {}
    for record in all_records:
        if record.muscle_group not in seen_groups:
            recovery_records[record.muscle_group] = record
            seen_groups.add(record.muscle_group)
    
    # Calculate recovery percentage for each muscle using non-linear J-curve model
    for muscle_group in all_muscle_groups:
        if muscle_group in recovery_records:
            record = recovery_records[muscle_group]
            record.update_recovery_status()
            
            if record.is_recovered or not record.recovery_until:
                recovery_progress[muscle_group] = 100.0
            else:
                workout_time = record.source_workout.datetime if record.source_workout else record.created_at
                total_duration = record.recovery_until - workout_time
                elapsed = timezone.now() - workout_time
                
                if total_duration.total_seconds() <= 0:
                    recovery_progress[muscle_group] = 100.0
                else:
                    # Non-linear recovery curve (J-curve model)
                    linear_progress = elapsed.total_seconds() / total_duration.total_seconds()
                    
                    if linear_progress <= 0.3:
                        non_linear_progress = linear_progress * 0.7
                    elif linear_progress <= 0.7:
                        non_linear_progress = 0.21 + (linear_progress - 0.3) * 1.225
                    else:
                        non_linear_progress = 0.7 + (linear_progress - 0.7) * 1.0
                    
                    percentage = non_linear_progress * 100
                    recovery_progress[muscle_group] = min(100.0, max(0.0, round(percentage, 2)))
        else:
            recovery_progress[muscle_group] = 100.0
    
    return recovery_progress


def create_workout_muscle_recovery(user, workout, condition, recovery_progress_dict):
    """
    Create WorkoutMuscleRecovery entries for all muscle groups.
    condition: 'pre' or 'post'
    recovery_progress_dict: {muscle_group: percentage}
    """
    all_muscle_groups = [choice[0] for choice in Exercise.MUSCLE_GROUPS]
    
    records = []
    for muscle_group in all_muscle_groups:
        progress = recovery_progress_dict.get(muscle_group, 100.0)
        record, created = WorkoutMuscleRecovery.objects.update_or_create(
            user=user,
            workout=workout,
            muscle_group=muscle_group,
            condition=condition,
            defaults={
                'recovery_progress': progress
            }
        )
        records.append(record)
    
    return records


def recalculate_workout_metrics(workout):
    """
    Recalculate calories and muscle recovery for a completed workout.
    Only runs if workout is done and not a rest day.
    Also recalculates if workout was completed in the last 4 days (for editing scenarios).
    """
    if workout.is_done and not workout.is_rest_day:
        workout_datetime = workout.datetime or workout.created_at
        time_diff = timezone.now() - workout_datetime
        days_since_workout = time_diff.days
        
        if days_since_workout <= 4 and time_diff.total_seconds() >= 0:
            calories_burned = calculate_workout_calories(workout)
            workout.calories_burned = calories_burned
            workout.save(update_fields=['calories_burned'])
            
            workout.calculate_muscle_recovery()
            workout.calculate_cns_recovery()


def calculate_workout_exercise_1rm(workout_exercise):
    """
    Calculate 1RM for a workout exercise.
    Gets all non-warmup sets, calculates 1RM for each, returns the highest.
    """
    sets = ExerciseSet.objects.filter(
        workout_exercise=workout_exercise,
        is_warmup=False
    ).exclude(weight=0).exclude(reps=0)
    
    if not sets.exists():
        return None
    
    max_1rm = None
    for exercise_set in sets:
        one_rm = calculate_one_rep_max(exercise_set.weight, exercise_set.reps)
        if one_rm is not None:
            if max_1rm is None or one_rm > max_1rm:
                max_1rm = one_rm
    
    return max_1rm


def get_rest_timer_state(workout):
    """
    Get rest timer state for active workout.
    Returns last set timestamp and exercise category.
    """
    if not workout or workout.is_done:
        return {
            "last_set_timestamp": None,
            "last_exercise_category": None,
            "elapsed_seconds": 0,
            "is_paused": False
        }
    
    last_set = ExerciseSet.objects.filter(
        workout_exercise__workout=workout
    ).select_related(
        'workout_exercise',
        'workout_exercise__exercise'
    ).order_by('-created_at', '-id').first()
    
    if not last_set:
        return {
            "last_set_timestamp": None,
            "last_exercise_category": None,
            "elapsed_seconds": 0,
            "is_paused": False
        }
    
    exercise = last_set.workout_exercise.exercise
    category = exercise.category if exercise and exercise.category else 'isolation'
    
    is_paused = workout.rest_timer_paused_at is not None
    if is_paused:
        elapsed_seconds = int((workout.rest_timer_paused_at - last_set.created_at).total_seconds())
    else:
        now = timezone.now()
        elapsed_seconds = int((now - last_set.created_at).total_seconds())
    
    rest_status = calculate_rest_status(elapsed_seconds, category)
    
    return {
        "last_set_timestamp": last_set.created_at.isoformat(),
        "last_exercise_category": category,
        "elapsed_seconds": elapsed_seconds,
        "rest_status": rest_status,
        "is_paused": is_paused
    }
