from django.db import models

from core.models import TimestampedModel
# Create your models here.

from user.models import CustomUser
from exercise.models import Exercise
class Workout(TimestampedModel):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    duration = models.PositiveIntegerField(default=0) ## duration is the time in seconds that the workout took
    intensity = models.CharField(max_length=255, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]) ## intensity is the intensity of the workout
    notes = models.TextField(blank=True, null=True) ## notes is a text field that the user can add to the workout
    is_done = models.BooleanField(default=False) ## is_done is a boolean field that indicates whether the workout has been completed


class WorkoutExercise(TimestampedModel):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)  # Link to Exercise template
    order = models.PositiveIntegerField(default=0)
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
        