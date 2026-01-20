from rest_framework import serializers
from .models import Achievement, UserAchievement, PersonalRecord, ExerciseStatistics, UserStatistics
from exercise.serializers import ExerciseSerializer


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement master data."""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    rarity_display = serializers.CharField(source='get_rarity_display', read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True, allow_null=True)

    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'description', 'icon',
            'category', 'category_display',
            'rarity', 'rarity_display',
            'requirement_value', 'exercise', 'exercise_name',
            'muscle_group', 'points', 'is_hidden', 'order'
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user's earned achievements."""
    achievement = AchievementSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = [
            'id', 'achievement', 'earned_at',
            'current_progress', 'earned_value',
            'is_notified', 'progress_percentage'
        ]

    def get_progress_percentage(self, obj):
        """Calculate progress as percentage towards achievement."""
        if obj.achievement.requirement_value <= 0:
            return 100
        progress = (float(obj.current_progress) / float(obj.achievement.requirement_value)) * 100
        return min(100, round(progress, 1))


class AchievementProgressSerializer(serializers.Serializer):
    """Serializer for achievement with user's progress (earned or not)."""
    achievement = AchievementSerializer()
    is_earned = serializers.BooleanField()
    current_progress = serializers.DecimalField(max_digits=10, decimal_places=2)
    progress_percentage = serializers.FloatField()
    earned_at = serializers.DateTimeField(allow_null=True)
    earned_value = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)


class PersonalRecordSerializer(serializers.ModelSerializer):
    """Serializer for personal records."""
    exercise = ExerciseSerializer(read_only=True)
    exercise_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = PersonalRecord
        fields = [
            'id', 'exercise', 'exercise_id',
            'best_weight', 'best_weight_reps', 'best_weight_date',
            'best_one_rep_max', 'best_one_rep_max_weight',
            'best_one_rep_max_reps', 'best_one_rep_max_date',
            'best_set_volume', 'best_set_volume_date',
            'total_volume', 'total_sets', 'total_reps',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PersonalRecordSummarySerializer(serializers.ModelSerializer):
    """Lightweight PR serializer for lists."""
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    exercise_id = serializers.UUIDField(source='exercise.id', read_only=True)

    class Meta:
        model = PersonalRecord
        fields = [
            'id', 'exercise_id', 'exercise_name',
            'best_weight', 'best_one_rep_max', 'total_volume'
        ]


class ExerciseStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for global exercise statistics."""
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    exercise_id = serializers.UUIDField(source='exercise.id', read_only=True)

    class Meta:
        model = ExerciseStatistics
        fields = [
            'id', 'exercise_id', 'exercise_name',
            'total_users', 'weight_percentiles', 'one_rm_percentiles',
            'volume_percentiles', 'average_weight', 'average_one_rm',
            'median_weight', 'median_one_rm', 'last_calculated'
        ]


class UserExerciseRankingSerializer(serializers.Serializer):
    """Serializer for a user's ranking on a specific exercise."""
    exercise_id = serializers.UUIDField()
    exercise_name = serializers.CharField()
    user_best_weight = serializers.DecimalField(max_digits=7, decimal_places=2)
    user_best_one_rm = serializers.DecimalField(max_digits=7, decimal_places=2)
    weight_percentile = serializers.IntegerField(allow_null=True)
    one_rm_percentile = serializers.IntegerField(allow_null=True)
    total_users = serializers.IntegerField()
    percentile_message = serializers.CharField()


class UserStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for user's overall statistics."""

    class Meta:
        model = UserStatistics
        fields = [
            'id', 'total_workouts', 'total_workout_duration',
            'total_volume', 'total_sets', 'total_reps',
            'current_streak', 'longest_streak', 'last_workout_date',
            'total_achievements', 'total_points',
            'total_prs', 'prs_this_month',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for leaderboard entries."""
    rank = serializers.IntegerField()
    user_id = serializers.UUIDField()
    display_name = serializers.CharField()
    value = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_current_user = serializers.BooleanField()


class NewAchievementNotificationSerializer(serializers.Serializer):
    """Serializer for new achievement notifications."""
    achievement = AchievementSerializer()
    earned_at = serializers.DateTimeField()
    earned_value = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    message = serializers.CharField()


class PRUpdateResultSerializer(serializers.Serializer):
    """Serializer for PR update results (returned after set is added)."""
    is_new_pr = serializers.BooleanField()
    pr_type = serializers.CharField(allow_null=True)  # 'weight', 'one_rm', 'volume', or None
    old_value = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    new_value = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    exercise_name = serializers.CharField()
    new_achievements = NewAchievementNotificationSerializer(many=True)
