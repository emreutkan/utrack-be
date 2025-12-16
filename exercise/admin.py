from django.contrib import admin
from .models import Exercise

class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_muscle', 'category', 'difficulty_level', 'is_active')
    list_filter = ('primary_muscle', 'category', 'difficulty_level', 'equipment_type', 'is_active')
    search_fields = ('name', 'description')

admin.site.register(Exercise, ExerciseAdmin)
