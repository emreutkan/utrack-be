from django.contrib import admin
from .models import Achievement, UserAchievement, PersonalRecord, ExerciseStatistics, UserStatistics


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rarity', 'requirement_value', 'exercise', 'points', 'is_active']
    list_filter = ['category', 'rarity', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['category', 'order', 'requirement_value']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at', 'current_progress', 'is_notified']
    list_filter = ['is_notified', 'achievement__category', 'achievement__rarity']
    search_fields = ['user__email', 'achievement__name']
    ordering = ['-earned_at']
    raw_id_fields = ['user', 'achievement']


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'best_weight', 'best_one_rep_max', 'total_sets', 'updated_at']
    list_filter = ['exercise__primary_muscle']
    search_fields = ['user__email', 'exercise__name']
    ordering = ['-best_weight']
    raw_id_fields = ['user', 'exercise']


@admin.register(ExerciseStatistics)
class ExerciseStatisticsAdmin(admin.ModelAdmin):
    list_display = ['exercise', 'total_users', 'average_weight', 'median_weight', 'last_calculated']
    search_fields = ['exercise__name']
    ordering = ['-total_users']


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_workouts', 'current_streak', 'longest_streak', 'total_achievements', 'total_points']
    search_fields = ['user__email']
    ordering = ['-total_workouts']
    raw_id_fields = ['user']
