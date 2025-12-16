from django.contrib import admin
from .models import Workout, WorkoutExercise, ExerciseSet

class ExerciseSetInline(admin.TabularInline):
    model = ExerciseSet
    extra = 1

class WorkoutExerciseInline(admin.TabularInline):
    model = WorkoutExercise
    extra = 1
    # inlines can't be nested by default in Django admin, so this line doesn't do anything for nested inlines.
    # To edit sets, you'd typically go to the WorkoutExercise admin page.

class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_done') # Changed date_created to created_at
    list_filter = ('is_done', 'created_at') # Changed date_created to created_at
    search_fields = ('title', 'user__email')
    # inlines = [WorkoutExerciseInline] 

class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ('workout', 'exercise', 'order')
    list_filter = ('workout',)
    inlines = [ExerciseSetInline]

admin.site.register(Workout, WorkoutAdmin)
admin.site.register(WorkoutExercise, WorkoutExerciseAdmin)
admin.site.register(ExerciseSet)
