from django.urls import path
from .views import CreateWorkoutView, AddExerciseToWorkoutView, AddExerciseSetToWorkoutExerciseView, GetWorkoutView, GetActiveWorkoutView, DeleteExerciseSetView, DeleteWorkoutExerciseView, UpdateExerciseOrderView
urlpatterns = [
    path('create/', CreateWorkoutView.as_view(), name='create-workout'),
    path('list/', GetWorkoutView.as_view(), name='list-workouts'),
    path('<int:workout_id>/add_exercise/', AddExerciseToWorkoutView.as_view(), name='add-exercise'),
    path('exercise/<int:workout_exercise_id>/add_set/', AddExerciseSetToWorkoutExerciseView.as_view(), name='add-set'),
    path('active/', GetActiveWorkoutView.as_view(), name='get-active-workout'),     
    path('list/<int:workout_id>/', GetWorkoutView.as_view(), name='get-workout'),
    path('set/<int:set_id>/delete/', DeleteExerciseSetView.as_view(), name='delete-set'),
    path('exercise/<int:workout_exercise_id>/delete/', DeleteWorkoutExerciseView.as_view(), name='delete-workout-exercise'),
    # Changed from exercise/<id>/update_order to <workout_id>/update_order because the view expects workout_id
    path('<int:workout_id>/update_order/', UpdateExerciseOrderView.as_view(), name='update-exercise-order'),    
]
