from django.urls import path
from .views import CreateWorkoutView, AddExerciseToWorkoutView, AddExerciseSetToWorkoutExerciseView, GetWorkoutView, GetActiveWorkoutView, DeleteExerciseSetView, DeleteWorkoutExerciseView, UpdateExerciseOrderView, CompleteWorkoutView, DeleteWorkoutView, CheckTodayRestDayView, CreateTemplateWorkoutView, GetTemplateWorkoutsView, StartTemplateWorkoutView, UpdateWorkoutView, UpdateExerciseSetView, GetRestTimerStateView, CalendarView, GetAvailableYearsView, CalendarStatsView
urlpatterns = [
    path('create/', CreateWorkoutView.as_view(), name='create-workout'),
    path('list/', GetWorkoutView.as_view(), name='list-workouts'),
    path('<int:workout_id>/add_exercise/', AddExerciseToWorkoutView.as_view(), name='add-exercise'),
    path('exercise/<int:workout_exercise_id>/add_set/', AddExerciseSetToWorkoutExerciseView.as_view(), name='add-set'),
    path('active/', GetActiveWorkoutView.as_view(), name='get-active-workout'),
    path('active/rest-timer/', GetRestTimerStateView.as_view(), name='rest-timer-state'),
    path('list/<int:workout_id>/', GetWorkoutView.as_view(), name='get-workout'),
    # Calendar endpoints
    path('calendar/', CalendarView.as_view(), name='calendar-view'),
    path('calendar/stats/', CalendarStatsView.as_view(), name='calendar-stats'),
    path('years/', GetAvailableYearsView.as_view(), name='available-years'),
    path('set/<int:set_id>/update/', UpdateExerciseSetView.as_view(), name='update-set'),
    path('set/<int:set_id>/delete/', DeleteExerciseSetView.as_view(), name='delete-set'),
    path('exercise/<int:workout_exercise_id>/delete/', DeleteWorkoutExerciseView.as_view(), name='delete-workout-exercise'),
    # Changed from exercise/<id>/update_order to <workout_id>/update_order because the view expects workout_id
    path('<int:workout_id>/update_order/', UpdateExerciseOrderView.as_view(), name='update-exercise-order'),
    path('<int:workout_id>/update/', UpdateWorkoutView.as_view(), name='update-workout'),
    path('<int:workout_id>/complete/', CompleteWorkoutView.as_view(), name='complete-workout'),
    path('<int:workout_id>/delete/', DeleteWorkoutView.as_view(), name='delete-workout'),
    path('check-rest-day/', CheckTodayRestDayView.as_view(), name='check-today-rest-day'),
    # Template workout endpoints
    path('template/create/', CreateTemplateWorkoutView.as_view(), name='create-template-workout'),
    path('template/list/', GetTemplateWorkoutsView.as_view(), name='list-template-workouts'),
    path('template/start/', StartTemplateWorkoutView.as_view(), name='start-template-workout'),
]
