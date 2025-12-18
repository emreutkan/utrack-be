from django.db import models
from django.utils import timezone

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
##    body_parts_worked = models.JSONField(default=list, blank=True, null=True) ## body_parts_worked is a json field that contains the body parts worked in the workout


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
