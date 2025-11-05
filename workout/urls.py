from django.urls import path
from .views import CreateWorkoutView, AddExerciseToWorkoutView, AddExerciseSetToWorkoutExerciseView, GetWorkoutView

urlpatterns = [
    path('create/', CreateWorkoutView.as_view(), name='create-workout'),
    path('list/', GetWorkoutView.as_view(), name='list-workouts'),
    path('<int:workout_id>/add_exercise/', AddExerciseToWorkoutView.as_view(), name='add-exercise'),
    path('exercise/<int:workout_exercise_id>/add_set/', AddExerciseSetToWorkoutExerciseView.as_view(), name='add-set'),
]

