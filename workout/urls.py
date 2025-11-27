from django.urls import path
from .views import CreateWorkoutView, AddExerciseToWorkoutView

urlpatterns = [
    path('create/', CreateWorkoutView.as_view(), name='create-workout'),
    path('<int:workout_id>/add_exercise/', AddExerciseToWorkoutView.as_view(), name='add-exercise'),
]

